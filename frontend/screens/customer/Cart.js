import { Text, View, Pressable, Image, ScrollView, Platform, NativeModules } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useFocusEffect} from "@react-navigation/native";
import { useState, useEffect, useCallback} from "react";
import styles from "../../styles";
import cart from "../../styles/screens/cart";
import RazorpayCheckout from "react-native-razorpay";


function CartItemCard({ item, addingItemsToCart, removingItemsFromCart }) {
    return (
        <View style={cart.itemListCard}>
            <View style={cart.itemOverview}>
                <Text style={cart.itemName}>{item.food}</Text>
                <Text style={cart.itemPrice}>₹ {item.price}</Text>
                <View style={[cart.veg, { borderColor: item.food_type==="VEG"?"green":"red" }]}>
                    <Text style={{ color: item.food_type==="VEG"?"green":"red", fontWeight: "bold" }}>{item.food_type==="VEG"?"● Veg":"▲ Non-Veg"}</Text>
                </View>
            </View>

            <Image source={require("../../assets/android-icon-background.png")} style={cart.itemImage} resizeMode="cover" />

            <View style={cart.cardButtonsView}>
                <View style={cart.quantityView}>
                    <Pressable onPress={()=>removingItemsFromCart(item.food_id)} style={[cart.cardCountBtn, { backgroundColor: "#FF4911" }]}>
                        <Text style={cart.buttonText}>-1</Text>
                    </Pressable>

                    <View style={cart.quantityDisplay}>
                        <Text>Qty: {item.quantity}</Text>
                    </View>

                    <Pressable onPress={()=>addingItemsToCart(item.food_id)} style={[cart.cardCountBtn, {borderLeftWidth:2}, { backgroundColor: "#2FFF2F" }]}>
                        <Text style={cart.buttonText}>+1</Text>
                    </Pressable>
                </View>

                <View style={cart.subtotalView}>
                    <Text style={cart.subtotalText}>₹ {item.price * item.quantity}</Text>
                </View>
            </View>
        </View>
    );
}





export default function Cart({route}) {
    const navigation=useNavigation();
    const loggedInUserData = route.params?.userData;
    const token = loggedInUserData?.access_token;
    const [cartItems, setCartItems]=useState({}); //this holds the food id and count unlike itemsInCart that fetches all the other details about the food from the id
    const [paymentState, setPaymentState] = useState({ status: "idle", message: "", receipt: null });



   

    useFocusEffect(useCallback(()=>{

        async function getCartList(){
            try{
                const response = await fetch(`https://canteen-backend-xzko.onrender.com/cart`,{
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
                const data = await response.json();
                setCartItems(data);

            }catch(error){
                console.log(error);
            }
        }
        getCartList();
    },[]));

 async function removingItemsFromCart(id) {
    console.log(`id sent: ${id}`)
    const currentItem = cartItems?.items?.find(
        item => item.food_id === id
    );

 

    if (!currentItem) {
        console.log("Item not found in cart");
        return;
    }

    try {
        let response;

        if (currentItem.quantity === 1) {
            response = await fetch(`https://canteen-backend-xzko.onrender.com/cart/items/${currentItem.item_id}`,{
                    method: 'DELETE',
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
        } else {
            response = await fetch(`https://canteen-backend-xzko.onrender.com/cart/items/${currentItem.item_id}`,{
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        quantity: currentItem.quantity - 1
                    })
                }
            );
        }

        if (!response.ok) {
            console.log('something went wrong')
            return;
        }

        const data = await response.json();
        setCartItems(data);

    } catch (error) {
        console.log("Cannot connect to server:", error);
    }
}



    async function addingItemsToCart(id) {
            try{
                const response = await fetch(`https://canteen-backend-xzko.onrender.com/cart/items`,{
                    method:'POST',
                    headers:{
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`
                    },
                    body:JSON.stringify({
                        food_id: id,
                        quantity: 1,
                    })
                });
                if(!response.ok){
                    console.log('something went wrong');
                    return;
                }

                const data =await response.json();
                setCartItems(data);

            }catch(error){
                console.log(`cannot connect to server: ${error}`);
            }
    }


    async function placeOrder(paymentDetails){

        try{
            const response = await fetch(`https://canteen-backend-xzko.onrender.com/orders`,{
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if(!response.ok){
                const error = await response.json();
                throw new Error(error.detail || "Could not place the canteen order");
            }

            const order = await response.json();
            const receipt = { ...order, payment_id: paymentDetails.razorpay_payment_id };
            console.log("CANTEEN ORDER RECEIPT", receipt);
            setCartItems({ items: [] });
            setPaymentState({ status: "success", message: "Payment and order successful", receipt });
            return true;

        }catch(error){
            console.log("ORDER FAILED", error);
            setPaymentState({ status: "order-failed", message: `Payment succeeded, but the order could not be placed: ${error.message || "unknown error"}`, receipt: null });
            return false;
        }

    }

    async function pay(){
        if (paymentState.status === "processing") return;
        const nativeCheckoutAvailable = Boolean(NativeModules.RNRazorpayCheckout?.open);
        if (Platform.OS === "web" || !nativeCheckoutAvailable) {
            const message = Platform.OS === "web"
                ? "Razorpay checkout is available in the Android/iOS app, not Expo Web"
                : "Razorpay native module is missing. Rebuild the Android app after installing react-native-razorpay.";
            console.log("PAYMENT UNAVAILABLE", message);
            setPaymentState({ status: "failed", message, receipt: null });
            return;
        }
        setPaymentState({ status: "processing", message: "Starting secure payment...", receipt: null });

        try {
            const response = await fetch(`https://canteen-backend-xzko.onrender.com/payments/orders`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });
            const paymentOrder = await response.json();
            if (!response.ok) throw new Error(paymentOrder.detail || "Could not start payment");

            console.log("RAZORPAY ORDER CREATED", paymentOrder);
            const paymentResult = await RazorpayCheckout.open({
                key: paymentOrder.key_id,
                amount: paymentOrder.amount,
                currency: paymentOrder.currency,
                name: "Canteen App",
                description: "Canteen order payment",
                order_id: paymentOrder.order_id,
            });
            console.log("RAZORPAY PAYMENT SUCCESS", paymentResult);

            const verifyResponse = await fetch(`https://canteen-backend-xzko.onrender.com/payments/verify`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(paymentResult)
            });
            const verification = await verifyResponse.json();
            if (!verifyResponse.ok || !verification.verified) {
                throw new Error(verification.detail || "Payment verification failed");
            }
            console.log("PAYMENT VERIFIED", verification);
            await placeOrder(paymentResult);
        } catch (error) {
            console.log("PAYMENT FAILED OR CANCELLED", error);
            setPaymentState({ status: "failed", message: error.description || error.message || "Payment failed or was cancelled", receipt: null });
        }
    }


    const totalItems=cartItems.items?.reduce((total, item) => total + item.quantity, 0);
    const totalPrice= cartItems.items?.reduce((total, item) => total + item.price * item.quantity, 0);


  
    return (
        <SafeAreaView style={cart.container}>
            <View style={styles.defaultView}>
                <View style={styles.appBar}>
                    <Text style={cart.headerText}>Your Cart</Text>
                    <Pressable style={cart.backBtn} onPress={() => navigation.popTo('Home', {userData:loggedInUserData},{merge: true})}><Text>Back</Text></Pressable>
                </View>

                <ScrollView style={cart.itemsList} contentContainerStyle={cart.itemsListContent}>
                    {cartItems.items?.length === 0 ? (
                        <View style={cart.emptyCart}>
                            <Text style={cart.emptyCartText}>Your cart is empty!</Text>
                            <Pressable style={cart.shopBtn} onPress={()=>navigation.popTo('Home', {userData:loggedInUserData},{merge: true})}><Text>Go back to menu</Text></Pressable>
                        </View>
                    ) : (
                        cartItems.items?.map(item => <CartItemCard key={item.item_id} item={item} addingItemsToCart={addingItemsToCart} removingItemsFromCart={removingItemsFromCart} />)
                    )}
                </ScrollView>

                {cartItems.items?.length > 0 && (
                    <View style={cart.checkoutView}>
                        <View>
                            <Text>Total ({totalItems} items)</Text>
                            <Text style={cart.totalPrice}>₹ {totalPrice}</Text>
                        </View>
                        <Pressable style={cart.checkoutBtn} onPress={pay} disabled={paymentState.status === "processing"}>
                            <Text style={cart.checkoutBtnText}>{paymentState.status === "processing" ? "Processing..." : "Place Order →"}</Text>
                        </Pressable>
                    </View>
                )}

                {paymentState.status !== "idle" && (
                    <View style={[cart.paymentResult, paymentState.status === "success" ? cart.paymentSuccess : cart.paymentFailure]}>
                        <Text style={cart.paymentResultTitle}>{paymentState.status === "success" ? "Order confirmed" : paymentState.status === "processing" ? "Payment in progress" : paymentState.status === "order-failed" ? "Order failed after payment" : "Payment failed"}</Text>
                        <Text>{paymentState.message}</Text>
                        {paymentState.receipt && (
                            <View style={cart.receipt}>
                                <Text>Receipt: {paymentState.receipt.order_id}</Text>
                                <Text>Paid: ₹ {paymentState.receipt.total_amount}</Text>
                                <Text>Payment ID: {paymentState.receipt.payment_id}</Text>
                                <Text>Items: {paymentState.receipt.items?.length || 0}</Text>
                            </View>
                        )}
                    </View>
                )}
            </View>
        </SafeAreaView>
    );
}
