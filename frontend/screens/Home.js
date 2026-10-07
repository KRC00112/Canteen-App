import { Text, View, TextInput, Pressable } from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import styles from "../styles";
import home from "../styles/screens/home";
import canteenFoodList from "../canteenFoodList";
import { useState } from "react";
import { ScrollView } from "react-native";


export default function Home(){

    const [foodList, setFoodList]=useState(canteenFoodList);
    
    return(
        <SafeAreaView style={home.container}>
            <View style={styles.defaultView}>
                <View style={home.nonScrollable}> 
                    <View style={styles.appBar}>
                        <Text>Welcome John Doe!</Text>
                    </View>
                    <View style={home.searchAndFilter}>
                        <TextInput
                            style={[styles.inputText, {flex:7}]}
                            placeholder='Enter Food Name...'
                        />
                        <Pressable style={home.filterBtn}><Text>Filter</Text></Pressable>
                    </View>
                </View>
                <ScrollView style={home.itemsList}>
                    {foodList.map(item=>{
                        return(
                            <View key={item.name} style={home.itemListCard}>
                                <Text>{item.name}</Text>
                            </View>
                            
                        );
                    })}
                </ScrollView>
            </View>            
        </SafeAreaView>
    );
}