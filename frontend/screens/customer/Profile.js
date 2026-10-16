// Profile.js
import { Text, View } from "react-native";
import { useState, useEffect } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import profileStyles from "../../styles/screens/profile";
import styles from "../../styles";


const STATUS_COLORS = {
  active: '#B6D7A8',
  inactive: '#D9D9D9',
  suspended: '#EA9999',
};

export default function Profile({ route }) {
  const token = route?.params?.userData?.access_token;
  const [profileData, setProfileData] = useState(null);

  useEffect(() => {
    async function getProfileData() {
      try {
        const response = await fetch("https://canteen-backend-xzko.onrender.com/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          console.log("something went wrong");
          return;
        }

        setProfileData(await response.json());
      } catch (error) {
        console.log("cannot connect to server");
      }
    }
    getProfileData();
  }, [token]);

  if (!profileData) {
    return (
      <SafeAreaView style={profileStyles.container}>
        <Text style={profileStyles.empty}>Loading...</Text>
      </SafeAreaView>
    );
  }

  const status = profileData.account_status;

  return (
    <SafeAreaView style={profileStyles.container} edges={['top', 'left', 'right']}>
        <View style={styles.defaultView}>

        
      <Text style={profileStyles.heading}>My Profile</Text>

      <View style={profileStyles.card}>
        <View style={profileStyles.headerCard}>
          <View style={profileStyles.avatar}>
            <Text style={profileStyles.avatarText}>
              {profileData.username?.[0]?.toUpperCase()}
            </Text>
          </View>
          <View>
            <Text style={profileStyles.username}>{profileData.username}</Text>
            <View style={profileStyles.badge}>
              <Text style={profileStyles.badgeText}>{profileData.role}</Text>
            </View>
          </View>
        </View>
      </View>

      <View style={profileStyles.card}>
        <View style={profileStyles.row}>
          <Text style={profileStyles.label}>Institute ID</Text>
          <Text style={profileStyles.value}>{profileData.institute_id}</Text>
        </View>

        <View style={[profileStyles.row, profileStyles.rowBorder]}>
          <Text style={profileStyles.label}>Status</Text>
          <View
            style={[
              profileStyles.badge,
              { marginTop: 0, backgroundColor: STATUS_COLORS[status?.toLowerCase()] ?? 'white' },
            ]}
          >
            <Text style={profileStyles.badgeText}>{status}</Text>
          </View>
        </View>

        <View style={[profileStyles.row, profileStyles.rowBorder]}>
          <Text style={profileStyles.label}>Member since</Text>
          <Text style={profileStyles.value}>
            {new Date(profileData.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      </View>
    </SafeAreaView>
  );
}