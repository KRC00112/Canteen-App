// Orders.js
import { Text, View, ScrollView } from "react-native";
import { useState, useEffect } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import orderStyles from "../../styles/screens/orders"
import styles from "../../styles";


// adjust keys to match your backend's status values
const STATUS_COLORS = {
  pending: '#FFD966',
  preparing: '#9FC5E8',
  ready: '#B6D7A8',
  completed: '#D9D9D9',
  cancelled: '#EA9999',
};

export default function Orders({ route }) {
  const token = route?.params?.userData?.access_token;
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    async function fetchOrders() {
      try {
        const response = await fetch("https://canteen-backend-xzko.onrender.com/orders", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          console.error("Failed to fetch orders:", response.status);
          return; // don't parse an error body as orders
        }

        setOrders(await response.json());
      } catch (error) {
        console.error("Error fetching orders:", error);
      }
    }
    fetchOrders();
  }, [token]);

  return (
    <SafeAreaView style={orderStyles.container} edges={['top', 'left', 'right']}>
      <View style={styles.defaultView}>
      <Text style={orderStyles.heading}>My Orders</Text>
        <ScrollView>
            {orders.length === 0 && <Text style={orderStyles.empty}>No orders yet</Text>}

            {orders.map(item => (
            <View key={item.order_id} style={orderStyles.card}>
                <View style={orderStyles.cardHeader}>
                <Text style={orderStyles.orderId}>#{item.order_id}</Text>
                <View
                    style={[
                    orderStyles.statusBadge,
                    { backgroundColor: STATUS_COLORS[item.status?.toLowerCase()] ?? 'white' },
                    ]}
                >
                    <Text style={orderStyles.statusText}>{item.status}</Text>
                </View>
                </View>

                <View style={orderStyles.cardBody}>
                <Text style={orderStyles.label}>Placed on</Text>
                <Text style={orderStyles.value}>
                    {new Date(item.created_at).toLocaleString()}
                </Text>
                </View>

                <View style={orderStyles.totalRow}>
                <Text style={orderStyles.label}>Total</Text>
                <Text style={orderStyles.totalText}>₹{item.total_amount}</Text>
                </View>
            </View>
            ))}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}