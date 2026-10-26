import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import StudentsList from './StudentsList';
import FacultyList from './FacultyList';
import StaffList from './StaffList';
import { SafeAreaView } from 'react-native-safe-area-context';
const Tab = createBottomTabNavigator();

export default function AdminTabs({ route }) {
  const userData = route.params?.userData;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFF8E7' }} edges={['top']}>
      <Tab.Navigator
        screenOptions={({ route: tabRoute }) => ({
        headerShown: false,
        tabBarPosition: 'top',
        tabBarActiveTintColor: '#111111',
        tabBarInactiveTintColor: '#666666',
        tabBarLabelStyle: { fontWeight: '900', fontSize: 11 },
        tabBarIcon: ({ color, focused }) => {
          const iconName = tabRoute.name === 'Students'
            ? (focused ? 'people' : 'people-outline')
            : tabRoute.name === 'Faculty'
              ? (focused ? 'school' : 'school-outline')
              : (focused ? 'briefcase' : 'briefcase-outline');

          return <Ionicons name={iconName} size={18} color={color} />;
        },
        tabBarShowLabel: true,
        tabBarStyle: {
          height: 64,
          paddingTop: 6,
          paddingBottom: 6,
          backgroundColor: '#FFF8E7',
          borderBottomWidth: 3,
          borderBottomColor: '#111111',
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
    </SafeAreaView>
  );
}
