import { View, Text } from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import styles from "../../../styles"
import home from "../../../styles/screens/home"

import {useEffect, useState} from "react";
import { ScrollView } from "react-native";
import { AdminUserCard } from "../../../components/AdminDataCard";


export default function FacultyList({route}){

    const loggedInUserData = route?.params?.userData;
    const token = loggedInUserData?.access_token;
    const [facultyList, setFacultyList]=useState([]);

    useEffect(() => {
        async function getUsersList() {
            
            const response=await fetch('https://canteen-backend-xzko.onrender.com/admin/users?role=FACULTY',{
                headers:{
                    'Authorization': `Bearer ${token}`
                }
            });
            const data =await response.json();
            setFacultyList(data);
            
        }

        getUsersList();

    },[token]);

    return(
        <SafeAreaView style={home.container} edges={['top', 'left', 'right']}>
            <View style={styles.defaultView}>
                <ScrollView>
                    {facultyList?.map(member=>{
                        return(
                            <AdminUserCard key={member.id} user={member} />
                           
                        );
                    })}
                </ScrollView>
                
            </View>
        </SafeAreaView>
    );
}