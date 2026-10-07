import { Pressable, Text, View } from 'react-native';
import login from '../styles/screens/login';
import styles from '../styles'
import { TextInput } from 'react-native';
import {useNavigation} from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';


export default function Login(){
    const navigation = useNavigation();

    return(
        <SafeAreaView style={styles.container}> 
            <Text style={[styles.header]}>LOG IN</Text>
            
            <View style={styles.form}>
                <View style={styles.formInputComponent}>
                    <Text style={styles.formInputLabel}>Institude ID</Text>
                    <TextInput 
                        style={styles.inputText}
                        placeholder='Enter Institute ID...'
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
                <Pressable style={[styles.button, styles.formInputComponent]} onPress={()=>navigation.navigate('Home')}>
                    <Text style={styles.buttonText}>LOG IN!</Text>
                </Pressable>
                <Text style={styles.accountAvailabilityMessage}>
                    Don't have an account? <Text style={styles.link} onPress={() =>navigation.navigate('Register')}>Register here!</Text>
                </Text>

            </View>

        </SafeAreaView>
    );

}