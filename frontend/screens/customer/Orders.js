import { Text, View } from "react-native";
import { useState, useEffect } from "react";

export default function Orders({route}){

    const loggedInUserData = route?.params?.userData;
    const token = loggedInUserData?.access_token;
    const [ordersList, setOrdersList] = useState([]);

    useEffect(() => {

        async function fetchOrders() {
            try{
                const response = await fetch("https://canteen-backend-xzko.onrender.com/orders", {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if(!response.ok){
                    console.error("Failed to fetch orders:", response.status);
                }

                const data = await response.json();

                setOrdersList(data);

            }catch(error){
                console.error("Error fetching orders:", error);
            }
        }

        fetchOrders();

    },[token])

    return(
        <View><Text>Orders</Text></View>
    );
}