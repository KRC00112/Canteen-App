import { Alert, Pressable, Text, View, Platform } from 'react-native';
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
    

    async function sendData(){
    try{
        const response = await fetch(`https://canteen-backend-xzko.onrender.com/auth/login`,{
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
         
        if(!response.ok){
            if(Platform.OS==='web'){
                alert('Login Failed', "something went wrong");
                return;
            }
            Alert.alert('Login Failed', "something went wrong");
            console.log(response)
            return;
        }
        const data=await response.json();
        console.log(JSON.stringify(data));
        if (Platform.OS === 'web') {
                alert('Logged In Successfully!');
                navigation.popTo('Home', { userData: data });
        }else{

             Alert.alert(
                'Success', 'Logged In Successfully!', [
                    {
                        text: 'Go to Home',
                        onPress:()=>navigation.popTo('Home',{userData: data})
                    }
                ]
            );

        }

       
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
                <Pressable style={[styles.button, styles.formInputComponent]} onPress={sendData}>{/*replace braces values of onpress with sendData*/}
                    <Text style={styles.buttonText}>LOG IN!</Text>
                </Pressable>
                <Text style={styles.accountAvailabilityMessage}>
                    Don't have an account? <Text style={styles.link} onPress={() =>navigation.navigate('Register')}>Register here!</Text>
                </Text>

            </View>

        </SafeAreaView>
    );

}