import { Text, View, Pressable, Image, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useFocusEffect} from "@react-navigation/native";
import { useState, useEffect, useCallback} from "react";
import styles from "../../styles";
import cart from "../../styles/screens/cart";


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


    async function pay(){
        const response = await fetch(`https://canteen-backend-xzko.onrender.com/payments/orders`,{
            method: 'POST',
            headers: {
                Authorization: `******`
            }
        });

        const paymentOrder = await response.json();
        if (!response.ok) {
            console.log('Could not create payment order:', paymentOrder.detail);
            return;
        }

        console.log('Razorpay order created:', paymentOrder);
        // Pass paymentOrder to the native Razorpay checkout. Call placeOrder only
        // from the checkout success handler after payment verification.
    }

    async function placeOrder(){

        try{
            const response = await fetch(`https://canteen-backend-xzko.onrender.com/orders`,{
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if(!response.ok){
                console.log('something went wrong');
                return;
            }

            const data=await response.json();
            const delResponse = await fetch(`https://canteen-backend-xzko.onrender.com/cart`,{
                    method: 'DELETE',
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            if (!delResponse.ok){
                console.log('order placed but couldn\'t clear cart');
            }
            navigation.navigate('CustomerTabs', {
                userData: loggedInUserData, // for CustomerTabs and its tabs
                screen: 'Orders',
                // params: { userData: loggedInUserData }, // for Orders
            });

        }catch(error){
            console.log(`can't connect to server: ${error}`)
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
                        <Pressable style={cart.checkoutBtn} onPress={pay}>
                            <Text style={cart.checkoutBtnText}>Place Order →</Text>
                        </Pressable>
                    </View>
                )}
            </View>
        </SafeAreaView>
    );
}
