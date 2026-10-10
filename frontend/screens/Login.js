import { Alert, Pressable, Text, View } from 'react-native';
import login from '../styles/screens/login';
import styles from '../styles'
import { TextInput } from 'react-native';
import {useNavigation} from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useState } from 'react';


export default function Login(){
    const navigation = useNavigation();
    const [instituteID, setInstituteID]=useState("");
    const [password, setPassword]=useState("");
    

    async function getData(){
    try{
        const response = await fetch(`http://172.29.45.218:8000/auth/login`,{
            method: 'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({ 
                institute_id: instituteID,
                password: password 
            }
        )

        });
        // const data=await response.json();
        if(!response.ok){
            Alert.alert('Login Failed', "something went wrong");
            console.log(response)
            return;
        }

        Alert.alert(
            'Success', 'Logged In Successfully!', [
                {
                    text: 'Go to Login',
                    onPress:()=>navigation.navigate('Home')
                }
            ]
        );
    }catch(error){
        Alert.alert('connection Error', 'Unable to connect to server.  Please try again');
        console.log(error)
    }

    }
    

    return(
        <SafeAreaView style={styles.container}> 
            <Text style={[styles.header]}>LOG IN</Text>
            
            <View style={styles.form}>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Institude ID</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Institute ID...'
                        onChangeText={value=>setInstituteID(value)}
                    />
                </View>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Password</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Password...'
                        secureTextEntry={false}
                        onChangeText={value=>setPassword(value)}
                    />
                </View>
                <Pressable style={[styles.button, styles.formInputComponent]} onPress={getData}>
                    <Text style={styles.buttonText}>LOG IN!</Text>
                </Pressable>
                <Text style={styles.accountAvailabilityMessage}>
                    Don't have an account? <Text style={styles.link} onPress={() =>navigation.navigate('Register')}>Register here!</Text>
                </Text>

            </View>

        </SafeAreaView>
    );

}