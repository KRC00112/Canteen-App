import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import CustomerHome from './CustomerHome';
import Orders from './Orders';
import Profile from './Profile';

const Tab = createBottomTabNavigator();

export default function CustomerTabs({ route }) {
  const userData = route.params?.userData;

  return (
    <Tab.Navigator
      screenOptions={({ route: tabRoute }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#6D28D9',
        tabBarInactiveTintColor: '#6B7280',
        tabBarStyle: {
          height: 62,
          paddingTop: 6,
          paddingBottom: 8,
        },
        tabBarIcon: ({ color, size, focused }) => {
          let iconName;

          if (tabRoute.name === 'CustomerHome') {
            iconName = focused ? 'home' : 'home-outline';
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
        name="CustomerHome"
        component={CustomerHome}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen name="Orders" component={Orders} initialParams={{ userData }}/>
      <Tab.Screen name="Profile" component={Profile} initialParams={{ userData }}/>
    </Tab.Navigator>
  );
}
