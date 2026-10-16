import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';


const Tab = createBottomTabNavigator();

export default function AdminTabs({ route }) {
  const insets = useSafeAreaInsets();
  const userData = route.params?.userData;

  return (
    <Tab.Navigator
      screenOptions={({ route: tabRoute }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#6D28D9',
        tabBarInactiveTintColor: '#6B7280',
        tabBarStyle: {
          height: 62+ insets.bottom,
          paddingTop: 6,
          paddingBottom: Math.max(insets.bottom, 8),
        },
        tabBarIcon: ({ color, size, focused }) => {
          let iconName;

          if (tabRoute.name === 'Menu') {
            iconName = focused ? 'list' : 'list-outline';
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
        initialParams={{ userData }}/>
      <Tab.Screen 
        name="Profile" 
        component={Profile} 
        initialParams={{ userData }}/>
    </Tab.Navigator>
  );
}
