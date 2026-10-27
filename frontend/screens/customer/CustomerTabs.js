import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import CustomerHome from './CustomerHome';
import Orders from './Orders';
import Profile from './Profile';
import { useSafeAreaInsets } from 'react-native-safe-area-context';


const Tab = createBottomTabNavigator();

export default function CustomerTabs({ route }) {
  const insets = useSafeAreaInsets();
  const userData = route.params?.userData;

  return (
    <Tab.Navigator
      screenOptions={({ route: tabRoute }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#111111',
        tabBarInactiveTintColor: '#666666',
        tabBarLabelStyle: { fontWeight: '900', fontSize: 11 },
        tabBarStyle: {
          height: 68 + insets.bottom,
          paddingTop: 8,
          paddingBottom: Math.max(insets.bottom, 8),
          backgroundColor: '#FFD43B',
          borderTopWidth: 3,
          borderTopColor: '#111111',
        },
        tabBarIcon: ({ color, size, focused }) => {
          let iconName;

          if (tabRoute.name === 'Menu') {
            iconName = focused ? 'menu' : 'menu-outline';
          } else if (tabRoute.name === 'Orders') {
            iconName = focused ? 'receipt' : 'receipt-outline';
          } else {
            iconName = focused ? 'person' : 'person-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="Menu"
        component={CustomerHome}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Menu' }}
      />
      <Tab.Screen 
        name="Orders" 
        component={Orders} 
        initialParams={{ userData }}
      />

      <Tab.Screen 
        name="Profile" 
        component={Profile} 
        initialParams={{ userData }}
      />
    </Tab.Navigator>
  );
}
