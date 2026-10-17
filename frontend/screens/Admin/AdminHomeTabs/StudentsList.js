import { View, Text } from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import styles from "../../../styles"
import home from "../../../styles/screens/home"

import {useEffect, useState} from "react";
import { ScrollView } from "react-native";


export default function StudentsList({route}){

    const loggedInUserData = route?.params?.userData;
    const token = loggedInUserData?.access_token;
    const [studentsList, setStudentsList]=useState();

    useEffect(() => {
        async function getUsersList() {
            
            const response=await fetch('https://canteen-backend-xzko.onrender.com/admin/users?role=STUDENT',{
                headers:{
                    'Authorization': `Bearer ${token}`
                }
            });
            const data =await response.json();
            setStudentsList(data);
            
        }

        getUsersList();

    },[token]);

    return(
        <SafeAreaView style={home.container} edges={['top', 'left', 'right']}>
            <View style={styles.defaultView}>
                <ScrollView>
                    {studentsList?.map(student=>{
                        return(
                            <Text key={student.id}>{student.username}</Text>
                           
                        );
                    })}
                </ScrollView>
                
            </View>
        </SafeAreaView>
    );
}