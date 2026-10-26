import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AdminHomeTabs from './AdminHomeTabs/AdminHomeTabs';
import FoodItems from './FoodItems'

const Tab = createBottomTabNavigator();

export default function AdminTabs({ route }) {
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

          if (tabRoute.name === 'Users List') {
            iconName = focused ? 'people' : 'people-outline';
          }else if (tabRoute.name === 'Food List') {
            iconName = focused ? 'fast-food' : 'fast-food-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="Users List"
        component={AdminHomeTabs}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Users List' }}
      />

       <Tab.Screen
        name="Food List"
        component={FoodItems}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Food List' }}
      />

    </Tab.Navigator>
  );
}
