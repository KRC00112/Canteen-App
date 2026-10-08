import { Text, View, TextInput, Pressable,Image } from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import styles from "../styles";
import home from "../styles/screens/home";
import canteenFoodList from "../canteenFoodList";
import { useState } from "react";
import { ScrollView } from "react-native";




function ItemListCard({item}){
    const [cartCount, setCartCount]=useState(0);

    function incrementCartCount(){
        setCartCount(prev=>prev+1)
    }
    function decrementCartCount(){
        setCartCount(prev=>{
            if(prev<=0){
                return 0
            }
            return prev-1;
        })
    }

    return(
        <View key={item.id} style={home.itemListCard}>
            
            <View style={home.cardCountDisplay}>
                <Text>In cart: {cartCount}</Text>
            </View>
            <View style={home.itemOverview}>
                <Text style={home.itemName}>{item.name}</Text>
                <Text style={home.itemPrice}>₹ {item.price}</Text>
                <View style={[home.veg, { borderColor: item.type==="veg" ? 'green' : 'red' }]}>
                    <Text style={{ color: item.type==="veg" ? 'green' : 'red', fontWeight: 'bold' }}>
                        {item.type==="veg" ? '● Veg' : '▲ Non-Veg'}
                    </Text>
                </View>            
            </View>
            <Image 
                source={require("../assets/android-icon-background.png")}
                style={{ width: '100%', height: 200, overflow:'hidden'}}
                resizeMode="cover"
            />
            <View style={home.cardButtonsView}>
                <Pressable style={[home.cardButton, {backgroundColor:'#7DF9FF'}]}>
                    <Text style={{color:'black'}}>View details  🛈 </Text>
                </Pressable>
                
                <Pressable onPress={incrementCartCount} style={[home.cardCountBtn, {backgroundColor:'#2FFF2F'}]}>
                    <Text style={{color:'black'}}>+1</Text>
                </Pressable>

                <Pressable onPress={decrementCartCount} style={[home.cardCountBtn, {backgroundColor:'#FF4911'}]}>
                    <Text style={{color:'black'}}>-1</Text>
                </Pressable>
            </View>
        </View>

    );
}


function FilterForm({categories, handleCategorySelection, selectedCategories, handleItemTypeSelection, itemType, itemPriceLimits, handleMinPriceSelection, handleMaxPriceSelection}){

    return(
        <View >
            <View style={home.filterForm}>
                <Text>Preferences</Text>
                <View>
                    <Text>Select item type: </Text>
                    <View style={home.itemsGrouping}>
                        <Pressable onPress={()=>handleItemTypeSelection('all')} style={[home.filterPrefBtn, itemType==="all"?{backgroundColor:'blue'}:{backgroundColor:'yellow'}]}><Text>All</Text></Pressable>
                        <Pressable onPress={()=>handleItemTypeSelection('veg')} style={[home.filterPrefBtn, itemType==="veg"?{backgroundColor:'blue'}:{backgroundColor:'yellow'}]}><Text>Veg</Text></Pressable>
                        <Pressable onPress={()=>handleItemTypeSelection('non-veg')} style={[home.filterPrefBtn, itemType==="non-veg"?{backgroundColor:'blue'}:{backgroundColor:'yellow'}]}><Text>Non-Veg</Text></Pressable>
                    </View>
                </View>
                <View>
                    <Text>Select item category: </Text>
                    <View style={home.itemsGrouping}>
                        {categories.map(item=>{
                            return(
                                <Pressable key={item} style={[home.filterPrefBtn, selectedCategories.includes(item)?{backgroundColor:'blue'}:{backgroundColor:'yellow'}]} onPress={()=>handleCategorySelection(item)}><Text>{item}</Text></Pressable>
                            );
                        })}
                    </View>
                </View>
                
                <View>
                    <Text>Item price limit: </Text>
                    <View style={home.itemsGrouping}>
                        <TextInput style={styles.inputText} placeholder="Minimum..." onChangeText={value=>handleMinPriceSelection(value)}/>
                        <TextInput style={styles.inputText} placeholder="Maximum..." onChangeText={value=>handleMaxPriceSelection(value)}/>
                    </View>
                </View>
                {/* <Pressable style={styles.button}><Text style={styles.buttonText}>Apply</Text></Pressable> */}
                    
            </View>
        </View>
    );
}


export default function Home(){

    const [foodList, setFoodList]=useState(canteenFoodList);
    const [showFilterForm, setShowFilterForm]=useState(false);
    const [selectedCategories, setSelectedCategories]=useState([]);
    const [searchInput, setSearchInput]=useState("");
    const [itemType, setItemType]=useState("all");
    const [itemPriceLimits, setItemPriceLimits]=useState({
        min: 0,
        max: 1000
    })


    let categories=[];
    foodList.forEach(item=>{
        if(!categories.includes(item.category)){
            categories.push(item.category)
        }
    });


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
                />}
                <View style={home.nonScrollable}> 
                    <View style={styles.appBar}>
                        <Text>Welcome John Doe!</Text>
                    </View>
                    <View style={home.searchAndFilter}>
                        <TextInput
                            style={[styles.inputText, {flex:7}]}
                            placeholder='Enter Food Name...'
                            onChangeText={value=>handleSearchInput(value)}
                        />
                        <Pressable style={home.filterBtn} onPress={()=>setShowFilterForm(!showFilterForm)}><Text>Filter</Text></Pressable>
                    </View>
                </View>
                <ScrollView style={home.itemsList}>
                    {foodList.map(item=>{
                        const categoryMatches=selectedCategories.length===0 || selectedCategories.includes(item.category);
                        const typeMatches=itemType==="all" || itemType===item.type;
                         // TODO: Fix bad pattern where either one of min or max is missing and the other exists
                        const priceMatches=item.price>=itemPriceLimits.min && item.price<=itemPriceLimits.max; 
                        const searchInputMatch=item.name.includes(searchInput);  

                        if (categoryMatches && typeMatches && priceMatches && searchInputMatch) {
                            return <ItemListCard key={item.id} item={item} />;
                        }
                    })}
                </ScrollView>
            </View>            
        </SafeAreaView>
    );
}