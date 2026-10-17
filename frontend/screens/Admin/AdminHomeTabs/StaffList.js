import { View, Text } from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import styles from "../../../styles"
import home from "../../../styles/screens/home"

import {useEffect, useState} from "react";
import { ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';



export default function StaffList({route}){

    const loggedInUserData = route?.params?.userData;
    const token = loggedInUserData?.access_token;
    const [staffList, setStaffList]=useState();

    useEffect(() => {
        async function getUsersList() {
            
            const response=await fetch('https://canteen-backend-xzko.onrender.com/admin/users?role=CANTEEN_STAFF',{
                headers:{
                    'Authorization': `Bearer ${token}`
                }
            });
            const data =await response.json();
            setStaffList(data);
            
        }

        getUsersList();

    },[token]);

    return(
        <SafeAreaView style={home.container} edges={['top', 'left', 'right']}>
            <View style={styles.defaultView}>
                <View style={styles.addNewCard}>
                    <Ionicons name="add-circle-outline" size={28} color="black" />
                    <Text>Add New Staff Member</Text>
                </View>
                <ScrollView>
                    {staffList?.map(member=>{
                        return(
                            <Text key={member.id}>{member.username} </Text>
                           
                        );
                    })}
                </ScrollView>
                
            </View>
        </SafeAreaView>
    );
}