import { Pressable, Text, View, Alert } from 'react-native';
import register from '../styles/screens/register';
import styles from '../styles'
import { TextInput } from 'react-native';
import {useNavigation} from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useState } from 'react';

export default function Register(){
    const navigation = useNavigation();

    const [instituteID, setInstituteID]=useState("");
    const [username, setUsername]=useState("");
    const [password, setPassword]=useState("");
    const [confirmPassword, setConfirmPassword]=useState("");
    const [focus, setFocus]=useState(false);




    async function sendData(){
        try{
            const response=await fetch(`http://172.29.45.218:8000/auth/register`,{
                method: 'POST',
                headers:{
                    'Content-Type': 'application/json'
                },
                body:JSON.stringify({ 
                    institute_id: instituteID,
                    username: username,
                    password: password,
                    confirm_password: confirmPassword 
                }),
            });

            // const data=await response.json();
            if(!response.ok){
                Alert.alert('Registration Failed', "something went wrong");
                console.log(response)
                return;
            }

            Alert.alert(
                'Success', 'Your account has been created!', [
                    {
                        text: 'Go to Login',
                        onPress:()=>navigation.navigate('Login')
                    }
                ]);

        }catch(error){
            Alert.alert('connection Error', 'Unable to connect to server.  Please try again');
            console.log(error)
        }

    }

    return(
        <SafeAreaView style={styles.container}> 
            <Text style={[styles.header]}>REGISTER</Text>
            
            <View style={styles.form}>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel} >Institude ID</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Institute ID...'
                        onChangeText={value=>setInstituteID(value)}
                    />
                </View>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Username</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Username...'
                        onChangeText={value=>setUsername(value)}
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
                <View style={styles.formInputComponent}>
                    <View style={register.confirmPasswordLabels}>
                        <Text style={(focus===true && password!==confirmPassword)?register.confirmPasswordMismatchLabels:styles.formInputLabel}>Confirm Password</Text>
                        {(focus===true && password!==confirmPassword) && <Text style={(focus===true && password!==confirmPassword)?register.confirmPasswordMismatchLabels:styles.formInputLabel}>Password Mismatch</Text>}
                    </View>
                    <TextInput 
                        style={[styles.inputText, (focus===true && password!==confirmPassword) && register.inputTextMismatch]}
                        placeholder='Enter Password Again...'
                        secureTextEntry={false}
                        onFocus={()=>setFocus(true)}
                        onChangeText={value=>setConfirmPassword(value)}
                    />
                </View>
                <Pressable style={[styles.formInputComponent, styles.button]} onPress={sendData}>
                    <Text style={styles.buttonText}>REGISTER!</Text>
                </Pressable>
                <Text style={styles.accountAvailabilityMessage}>
                    Already have an account? <Text style={styles.link} onPress={() =>navigation.navigate('Login')}>Login here!</Text>
                </Text>
            </View>

        </SafeAreaView>
    );

}