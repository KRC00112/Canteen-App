import { Text, View, TextInput, Pressable,Image, StyleSheet } from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useFocusEffect } from "@react-navigation/native";
import styles from "../styles";
import home from "../styles/screens/home";
import canteenFoodList from "../canteenFoodList";
import { useState, useEffect,useCallback } from "react";
import { ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';
import CustomerHome from "./customer/CustomerHome";




export default function Home({route}){

    const navigation = useNavigation();

    const role = route.params?.userData?.role;
    // const token = loggedInUserData?.access_token;

    useEffect(() => {
        if (role === "STUDENT" || role === "FACULTY") {
            navigation.replace("CustomerHome", {userData: route.params?.userData});
        } else if (role === "CANTEEN_STAFF") {
            navigation.replace("StaffHome", {userData: route.params?.userData});
        }
    }, [role, route.params?.userData]);

    return (
        <View>
            <Text>Loading...</Text>
        </View>
    );

}