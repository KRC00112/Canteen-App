import { View, Text } from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import styles from "../../styles"
import home from "../../styles/screens/home"

import {useEffect, useState} from "react";
import { ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';



export default function FoodItems({route}){

    const loggedInUserData = route?.params?.userData;
    const token = loggedInUserData?.access_token;
    const [foodList, setFoodList]=useState();

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
    },[]);

    
    return(
        <SafeAreaView style={home.container} edges={['top', 'left', 'right']}>
            <View style={styles.defaultView}>
                <View style={styles.addNewCard}>
                        <Ionicons name="add-circle-outline" size={28} color="black" />
                        <Text>Add New Food Item</Text>
                </View>
                <ScrollView>
                    {foodList?.map(item=>{
                        return(
                            <Text key={item.id}>{item.name}</Text>
                           
                        );
                    })}
                </ScrollView>
            </View>
        </SafeAreaView>
    );
}