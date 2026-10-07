import { StatusBar } from 'expo-status-bar';
import { Text, View } from 'react-native';
import styles from './styles'

import Login from "./screens/Login"
import Register from "./screens/Register"
import Home from './screens/Home';

import {createStaticNavigation} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import {
  SafeAreaView,
  SafeAreaProvider,
  SafeAreaInsetsContext,
  useSafeAreaInsets,
} from 'react-native-safe-area-context';


const RootStack = createNativeStackNavigator({
  screens: {
    Login: {
      screen: Login,
      options:{
        headerShown:false,
      }
    },
    Register: {
      screen: Register,
      options:{
        headerShown:false,
      }
    },Home: {
      screen: Home,
      options:{
        headerShown:false,
      }
    },
  },
});

const Navigation = createStaticNavigation(RootStack);


export default function App() {
  return (
    <SafeAreaProvider >
        {/* <Login />  */}
        <Navigation/>

    </SafeAreaProvider>
  );
}


