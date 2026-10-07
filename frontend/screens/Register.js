import { Pressable, Text, View } from 'react-native';
import register from '../styles/screens/register';
import styles from '../styles'
import { TextInput } from 'react-native';
import {useNavigation} from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function Register(){
    const navigation = useNavigation();

    return(
        <SafeAreaView style={styles.container}> 
            <Text style={[styles.header]}>REGISTER</Text>
            
            <View style={styles.form}>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Institude ID</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Institute ID...'
                    />
                </View>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Username</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Username...'
                    />
                </View>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Password</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Password...'
                        secureTextEntry={true}
                    />
                </View>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Confirm Password</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Password Again...'
                        secureTextEntry={true}
                    />
                </View>
                <Pressable style={[styles.formInputComponent, styles.button]}>
                    <Text style={styles.buttonText}>REGISTER!</Text>
                </Pressable>
                <Text style={styles.accountAvailabilityMessage}>
                    Already have an account? <Text style={styles.link} onPress={() =>navigation.navigate('Login')}>Login here!</Text>
                </Text>
            </View>

        </SafeAreaView>
    );

}