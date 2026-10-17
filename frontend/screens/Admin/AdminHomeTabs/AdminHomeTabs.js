import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import StudentsList from './StudentsList';
import FacultyList from './FacultyList';
import StaffList from './StaffList';
const Tab = createBottomTabNavigator();

export default function AdminTabs({ route }) {
  const insets = useSafeAreaInsets();
  const userData = route.params?.userData;

  return (
    <Tab.Navigator
      screenOptions={({ route: tabRoute }) => ({
        headerShown: false,
        tabBarPosition: 'top',
        tabBarActiveTintColor: '#6D28D9',
        tabBarInactiveTintColor: '#6B7280',
        tabBarShowIcon: false,
        tabBarShowLabel: true,
        tabBarStyle: {
          height: 62 + insets.top,
          paddingTop: 6,
          paddingBottom: 6,
        },
      })}
    >
      <Tab.Screen
        name="Students"
        component={StudentsList}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Students List' }}
      />

      <Tab.Screen
        name="Faculty"
        component={FacultyList}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Faculty List' }}
      />

      <Tab.Screen
        name="Staff"
        component={StaffList}
        initialParams={{ userData }}
        options={{ tabBarLabel: 'Staff List' }}
      />

    </Tab.Navigator>
  );
}
