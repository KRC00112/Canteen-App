import { Text, View, Pressable, Image, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation} from "@react-navigation/native";
import { useState} from "react";
import styles from "../styles";
import cart from "../styles/screens/cart";
import { AddItemContext } from "../contexts/AddItemContext";
function CartItemCard({ item, count, addingItemsToCart, removingItemsFromCart }) {
    return (
        <View style={cart.itemListCard}>
            <View style={cart.itemOverview}>
                <Text style={cart.itemName}>{item.name}</Text>
                <Text style={cart.itemPrice}>₹ {item.price}</Text>
                <View style={[cart.veg, { borderColor: item.type==="veg"?"green":"red" }]}>
                    <Text style={{ color: item.type==="veg"?"green":"red", fontWeight: "bold" }}>{item.type==="veg"?"● Veg":"▲ Non-Veg"}</Text>
                </View>
            </View>

            <Image source={require("../assets/android-icon-background.png")} style={cart.itemImage} resizeMode="cover" />

            <View style={cart.cardButtonsView}>
                <View style={cart.quantityView}>
                    <Pressable onPress={()=>removingItemsFromCart(item.id)} style={[cart.cardCountBtn, { backgroundColor: "#FF4911" }]}>
                        <Text style={cart.buttonText}>-1</Text>
                    </Pressable>

                    <View style={cart.quantityDisplay}>
                        <Text>Qty: {count}</Text>
                    </View>

                    <Pressable onPress={()=>addingItemsToCart(item.id)} style={[cart.cardCountBtn, {borderLeftWidth:2}, { backgroundColor: "#2FFF2F" }]}>
                        <Text style={cart.buttonText}>+1</Text>
                    </Pressable>
                </View>

                <View style={cart.subtotalView}>
                    <Text style={cart.subtotalText}>₹ {item.price * count}</Text>
                </View>
            </View>
        </View>
    );
}

export default function Cart({route}) {
    const navigation=useNavigation();
    let canteenFoodList=route.params.canteenFoodList;
    const [cartItems, setCartItems]=useState(route.params.cartItems); //this holds the food id and count unlike itemsInCart that fetches all the other details about the food from the id

    function addingItemsToCart(id) {
        setCartItems(prev=>prev.map(item=>item.id===id?{...item, count: item.count + 1}: item));
    }

    function removingItemsFromCart(id) {
        setCartItems(prev=>prev.map(item=>item.id===id?{...item, count: item.count - 1} : item).filter(item=>item.count > 0));
    }

    const itemsInCart=cartItems.map(cartItem => {
        const foodItem=canteenFoodList.find(item => item.id === cartItem.id);
        return foodItem?{ ...foodItem, count: cartItem.count }:null;
    });

    const totalItems=itemsInCart.reduce((total, item) => total + item.count, 0);
    const totalPrice= itemsInCart.reduce((total, item) => total + item.price * item.count, 0);

    return (
        <SafeAreaView style={cart.container}>
            <View style={styles.defaultView}>
                <View style={styles.appBar}>
                    <Text style={cart.headerText}>Your Cart</Text>
                    <Pressable style={cart.backBtn} onPress={() => navigation.navigate('Home', {result:cartItems})}><Text>Back</Text></Pressable>
                </View>

                <ScrollView style={cart.itemsList} contentContainerStyle={cart.itemsListContent}>
                    {itemsInCart.length === 0 ? (
                        <View style={cart.emptyCart}>
                            <Text style={cart.emptyCartText}>Your cart is empty!</Text>
                            <Pressable style={cart.shopBtn} onPress={()=>navigation.navigate('Home', {result:cartItems})}><Text>Go back to menu</Text></Pressable>
                        </View>
                    ) : (
                        itemsInCart.map(item => <CartItemCard key={item.id} item={item} count={item.count} addingItemsToCart={addingItemsToCart} removingItemsFromCart={removingItemsFromCart} />)
                    )}
                </ScrollView>

                {itemsInCart.length > 0 && (
                    <View style={cart.checkoutView}>
                        <View>
                            <Text>Total ({totalItems} items)</Text>
                            <Text style={cart.totalPrice}>₹ {totalPrice}</Text>
                        </View>
                        <Pressable style={cart.checkoutBtn} onPress={() => navigation.navigate("Checkout", { cartItems })}>
                            <Text style={cart.checkoutBtnText}>Checkout →</Text>
                        </Pressable>
                    </View>
                )}
            </View>
        </SafeAreaView>
    );
}
