import { Text, View, TextInput, Pressable,Image, StyleSheet } from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useFocusEffect } from "@react-navigation/native";
import styles from "../styles";
import home from "../styles/screens/home";
import canteenFoodList from "../canteenFoodList";
import { useState, useEffect,useCallback } from "react";
import { ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';




function ItemListCard({item, addingItemsToCart, removingItemsFromCart, cartItems, handleDetailsCardVisibility, handleItemSelect}){

    
    function showCartCount(id){
        let count= (cartItems.items)?.find(x=>x.food_id===item.id)?.quantity
        if (count){
            return count;
        }
        return 0;
    }



    return(
        <View key={item.id} style={home.itemListCard}>
            
            <View style={home.cardCountDisplay}>
                <Text>In cart: {showCartCount(item.id)}</Text>
            </View>

            <View style={home.itemOverview}>
                <Text style={home.itemName}>{item.name}</Text>
                <Text style={home.itemPrice}>₹ {item.price}</Text>
                <View style={[home.veg, { borderColor: item.food_type==="VEG" ? 'green' : 'red' }]}>
                    <Text style={{ color: item.food_type==="VEG" ? 'green' : 'red', fontWeight: 'bold' }}>
                        {item.food_type==="VEG" ? '● Veg' : '▲ Non-Veg'}
                    </Text>
                </View>            
            </View>
            <Image 
                source={require("../assets/android-icon-background.png")}
                style={{ width: '100%', height: 200, overflow:'hidden'}}
                resizeMode="cover"
            />
            <View style={home.cardButtonsView}>
                <Pressable style={[home.cardButton, {backgroundColor:'#7DF9FF'}]} onPress={()=>{handleDetailsCardVisibility();handleItemSelect(item)}}>
                    <Ionicons name="information-circle-outline" size={21} color="black" />
                    <Text style={{ color: 'black' }}>View details </Text>
                </Pressable>
                
                <Pressable onPress={()=>{addingItemsToCart(item.id)}} style={[home.cardCountBtn, {backgroundColor:'#2FFF2F'}]}>
                    <Text style={{color:'black'}}>+1</Text>
                </Pressable>

                <Pressable onPress={()=>{removingItemsFromCart(item.id)}} style={[home.cardCountBtn, {backgroundColor:'#FF4911'}]}>
                    <Text style={{color:'black'}}>-1</Text>
                </Pressable>
            </View>
        </View>

    );
}


function MoreDetailsCard({ selectedItem, handleDetailsCardVisibility,addingItemsToCart, removingItemsFromCart }) {
    if (!selectedItem) return null;

    const {name, description, ingredients, avg_cooking_time_minutes, stock_status, stock_message, popular, food_type,price} = selectedItem;

    return (
        <View style={home.overlay}>
            <Pressable
                style={StyleSheet.absoluteFill}
                onPress={handleDetailsCardVisibility}
            />
            <View style={[home.popupForm, home.detailsCard]}>
                <Text style={home.detailsTitle}>{name}</Text>
                <Text style={home.detailsPrice}>₹ {price}</Text>

                {popular && (
                    <View style={home.filterPrefBtn}>
                        <Text style={{ fontWeight: 'bold' }}>★ Popular</Text>
                    </View>
                )}

                {description && <Text>{description}</Text>}

                 <View style={[home.veg, { borderColor: food_type==="VEG" ? 'green' : 'red' }]}>
                    <Text style={{ color: food_type==="VEG" ? 'green' : 'red', fontWeight: 'bold' }}>
                        {food_type==="VEG" ? '● Veg' : '▲ Non-Veg'}
                    </Text>
                </View> 

                {ingredients?.length > 0 && (
                    <View>
                        <Text style={{ fontWeight: 'bold' }}>Ingredients:</Text>
                        <View style={home.itemsGrouping}>
                            {ingredients.map(ing => (
                                <View key={ing} style={home.filterPrefBtn}>
                                    <Text>{ing}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                )}

                <Text>
                    <Text style={{ fontWeight: 'bold' }}>Estimated cooking time: </Text>
                    ~{avg_cooking_time_minutes} min
                </Text>

                {stock_status !== "IN_STOCK" && (
                    <Text style={{ color: 'red', fontWeight: 'bold' }}>
                        {stock_message}
                    </Text>
                )}
                <View style={[home.cardButtonsView,{borderTopWidth:0, gap:7}]}>
                    <Pressable
                        onPress={() => addingItemsToCart(selectedItem.id)}
                        style={[home.cardCountBtn, { backgroundColor: '#2FFF2F', borderWidth: 2 ,boxShadow: '4px 5px rgba(0, 0, 0)',}]}
                    >
                        <Text style={{ color: 'black' }}>+1</Text>
                    </Pressable>

                    <Pressable
                        onPress={() => removingItemsFromCart(selectedItem.id)}
                        style={[home.cardCountBtn, { backgroundColor: '#FF4911', borderWidth: 2, boxShadow: '4px 5px rgba(0, 0, 0)',  }]}
                    >
                        <Text style={{ color: 'black' }}>-1</Text>
                    </Pressable>
                </View>

            </View>
        </View>
    );
}

function FilterForm({categories, handleCategorySelection, selectedCategories, handleItemTypeSelection, itemType, itemPriceLimits, handleMinPriceSelection, handleMaxPriceSelection,handleFilterFormVisibility}){

    return(
        <View style={home.overlay} >
            <Pressable
                style={StyleSheet.absoluteFill}
                onPress={handleFilterFormVisibility}
            />
            <View style={home.popupForm}>
                <Text style={{fontWeight:'bold'}}>Preferences</Text>
                <View>
                    <Text style={{fontWeight:'bold'}}>Select item type: </Text>
                    <View style={home.itemsGrouping}>
                        <Pressable onPress={()=>handleItemTypeSelection('ALL')} style={[home.filterPrefBtn, itemType==="ALL"?{backgroundColor:'rgba(0,255,0,1)'}:{backgroundColor:'white'}]}><Text style={{fontWeight:'bold'}}>All</Text></Pressable>
                        <Pressable onPress={()=>handleItemTypeSelection('VEG')} style={[home.filterPrefBtn, itemType==="VEG"?{backgroundColor:'rgba(0,255,0,1)'}:{backgroundColor:'white'}]}><Text style={{fontWeight:'bold'}}>Veg</Text></Pressable>
                        <Pressable onPress={()=>handleItemTypeSelection('NON_VEG')} style={[home.filterPrefBtn, itemType==="NON_VEG"?{backgroundColor:'rgba(0,255,0,1)'}:{backgroundColor:'white'}]}><Text style={{fontWeight:'bold'}}>Non-Veg</Text></Pressable>
                    </View>
                </View>
                <View>
                    <Text style={{fontWeight:'bold'}}>Select item category: </Text>
                    <View style={home.itemsGrouping}>
                        {categories.map(item=>{
                            return(
                                <Pressable key={item} style={[home.filterPrefBtn, selectedCategories.includes(item)?{backgroundColor:'rgba(0,255,0,1)'}:{backgroundColor:'white'}]} onPress={()=>handleCategorySelection(item)}><Text style={{fontWeight:'bold'}}>{item}</Text></Pressable>
                            );
                        })}
                    </View>
                </View>
                
                <View>
                    <Text style={{fontWeight:'bold'}}>Item price limit: </Text>
                    <View style={home.itemsGrouping}>
                        <TextInput style={[styles.inputText, {fontWeight:'bold'}]} placeholder="Minimum..." onChangeText={value=>handleMinPriceSelection(value)}/>
                        <TextInput style={[styles.inputText, {fontWeight:'bold'}]} placeholder="Maximum..." onChangeText={value=>handleMaxPriceSelection(value)}/>
                    </View>
                </View>
                {/* <Pressable style={styles.button}><Text style={styles.buttonText}>Apply</Text></Pressable> */}
                    
            </View>
        </View>
    );
}


export default function Home({route}){

  


    const [selectedItem, setSelectedItem]=useState(null);
    const [foodList, setFoodList]=useState([]);
    const [showMoreDetailsCard, setShowMoreDetailsCard]=useState(false);
    const [showFilterForm, setShowFilterForm]=useState(false);
    const [selectedCategories, setSelectedCategories]=useState([]);
    const [searchInput, setSearchInput]=useState("");
    const [itemType, setItemType]=useState("ALL");
    const [itemPriceLimits, setItemPriceLimits]=useState({
        min: 0,
        max: 1000
    })
    const [cartItems, setCartItems]=useState({});
    const loggedInUserData = route.params?.userData;
    const token = loggedInUserData?.access_token;

    
    const navigation = useNavigation();
    

    useEffect(()=>{
        async function getFoodList(){
            try{
                const response = await fetch(`https://canteen-backend-xzko.onrender.com/menu`);
                const data = await response.json();
                setFoodList(data);

            }catch(error){
                console.log(error);
            }
        }
        getFoodList();
    },[])

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
    },[]))




    let categories=[];
    foodList.forEach(item=>{
        if(!categories.includes(item.category)){
            categories.push(item.category)
        }

    });

    function handleItemSelect(item){
        setSelectedItem(item)
    }

    function handleDetailsCardVisibility(){
        setShowMoreDetailsCard(!showMoreDetailsCard)
    }


async function removingItemsFromCart(id) {
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

    function handleCategorySelection(category){
        if(selectedCategories.includes(category)){
            return setSelectedCategories(selectedCategories.filter(item=>item!==category))
        }
        return setSelectedCategories(prev=>[...prev, category])
    }

    function handleItemTypeSelection(itemType){
        setItemType(itemType);

    }

    function handleMinPriceSelection(min){
        setItemPriceLimits({...itemPriceLimits,
            min: min
        })
    }

    function handleMaxPriceSelection(max){
        setItemPriceLimits({...itemPriceLimits,
            max: max
        })
    }

    function handleSearchInput(value){
        setSearchInput(value)
    }
  
    function handleFilterFormVisibility(){
        setShowFilterForm(!showFilterForm)
    }
    
    return(
        <SafeAreaView style={home.container}>
            <View style={styles.defaultView}>
                {showFilterForm && <FilterForm 
                    categories={categories} 
                    handleCategorySelection={handleCategorySelection} 
                    selectedCategories={selectedCategories}
                    handleItemTypeSelection={handleItemTypeSelection}
                    itemType={itemType}
                    itemPriceLimits={itemPriceLimits}
                    handleMinPriceSelection={handleMinPriceSelection}
                    handleMaxPriceSelection={handleMaxPriceSelection}
                    handleFilterFormVisibility={handleFilterFormVisibility}
                />}
                {showMoreDetailsCard && <MoreDetailsCard 
                    selectedItem={selectedItem} 
                    handleDetailsCardVisibility={handleDetailsCardVisibility}
                    addingItemsToCart={addingItemsToCart}
                    removingItemsFromCart={removingItemsFromCart}
                />}
                <View style={home.nonScrollable}> 
                    <View style={styles.appBar}>
                        <Text>Welcome {loggedInUserData?.username}!</Text>
                        <Pressable style={home.goToCartBtn} onPress={()=>navigation.navigate('Cart', {userData: loggedInUserData})}><Text>Cart</Text></Pressable>
                    </View>
                    <View style={home.searchAndFilter}>
                        <TextInput
                            style={[styles.inputText, {flex:7}]}
                            placeholder='Enter Food Name...'
                            onChangeText={value=>handleSearchInput(value)}
                        />
                        <Pressable style={home.filterBtn} onPress={handleFilterFormVisibility}><Text>Filter</Text></Pressable>
                    </View>
                </View>
                <ScrollView style={home.itemsList}>
                    {foodList.map(item=>{
                        const categoryMatches=selectedCategories.length===0 || selectedCategories.includes(item.category);
                        const typeMatches=itemType==="ALL" || itemType===item.food_type;
                         // TODO: Fix bad pattern where either one of min or max is missing and the other exists
                        const priceMatches=item.price>=itemPriceLimits.min && item.price<=itemPriceLimits.max; 
                        const searchInputMatch=item.name.includes(searchInput);  

                        if (categoryMatches && typeMatches && priceMatches && searchInputMatch) {
                            return <ItemListCard 
                                key={item.id} 
                                item={item} 
                                addingItemsToCart={addingItemsToCart}
                                removingItemsFromCart={removingItemsFromCart}
                                cartItems={cartItems}
                                handleDetailsCardVisibility={handleDetailsCardVisibility}
                                handleItemSelect={handleItemSelect}
                            />;
                        }
                    })}
                </ScrollView>
            </View>            
        </SafeAreaView>
    );
}