import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import StaffHome from './StaffHome';
import Profile from '../Profile';

const Tab = createBottomTabNavigator();

export default function StaffTabs({ route }) {
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
          const iconName = tabRoute.name === 'Orders'
            ? (focused ? 'receipt' : 'receipt-outline')
            : (focused ? 'person' : 'person-outline');

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="Orders"
        component={StaffHome}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Orders' }}
      />
      <Tab.Screen
        name="Profile"
        component={Profile}
        initialParams={{ userData }}
      />
    </Tab.Navigator>
  );
}
