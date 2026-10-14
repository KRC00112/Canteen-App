
import { View, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import home from "../../styles/screens/home";
import styles from "../../styles";
import { useCallback, useState } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { ScrollView } from "react-native";


function formatTime(timestamp) {
    if (!timestamp) return "-";
    return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(timestamp) {
    if (!timestamp) return "-";
    return new Date(timestamp).toLocaleDateString([], { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateTime(timestamp) {
    if (!timestamp) return "-";
    return `${formatDate(timestamp)}, ${formatTime(timestamp)}`;
}



function OrdersCard({ item }) {
    return (
        <View style={home.ordersCard}>
            <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <Text style={{ fontWeight: "900" }}>{item.order_id}</Text>
                <Text style={{ fontWeight: "bold" }}>{item.status}</Text>
            </View>

            <Text>{item.customer} (ID {item.institute_id})</Text>
            <Text>Placed: {formatDateTime(item.created_at)}</Text>
            {/* <Text>Ready by: {formatTime(item.estimated_ready_at)}</Text> */}

            <View>
                {item.items?.map((it, i) => (
                    <Text key={i}>{it.quantity} x {it.food ?? it.name}</Text>
                ))}
            </View>

            <Text style={{ fontWeight: "900" }}>Total: ₹ {item.total}</Text>
        </View>
    );
}

export default function StaffHome({route}){
    const loggedInUserData=route?.params?.userData;
    const token =loggedInUserData?.access_token;
    const [ordersList, setOrdersList]=useState([])



    useFocusEffect(useCallback(()=>{

        async function getOrdersList(){
        try{
            const response = await fetch(`https://canteen-backend-xzko.onrender.com/staff/orders`,{
                headers:{
                    Authorization: `Bearer ${token}`
                }
            });
            const data = await response.json();
            console.log(`the data: ${JSON.stringify(data)}`);

            if(!response.ok){
                console.log("something went wrong");      
                return;
            }

            setOrdersList(data);

        }catch(error){
            console.log(error);
        }
    }
    getOrdersList();

    const id = setInterval(getOrdersList, 10000);

    return () => clearInterval(id);  

    },[token]))

    // useEffect(()=>{
    //     async function getOrdersList(){
    //         try{
    //             const response = await fetch(`https://canteen-backend-xzko.onrender.com/staff/orders`);
    //             const data = await response.json();
    //             setFoodList(data);

    //         }catch(error){
    //             console.log(error);
    //         }
    //     }
    //     getOrdersList();
    // },[]);
    
    

    const stateCards = [
        { id: 1, name: "Placed", color: "#3B82F6" },
        { id: 2, name: "Preparing", color: "#F59E0B" },
        { id: 3, name: "Ready", color: "#10B981" },
        { id: 4, name: "Served", color: "#8B5CF6" },
    ];
    

    return(
         <SafeAreaView style={home.container}>
            <View style={styles.defaultView}>
                <Text>Staff Id: {loggedInUserData.username}</Text>
                <View style={home.statusCards}>
                    
                    {stateCards.map(item=>{
                        return (

                        <View style={[home.statusCard, {backgroundColor:item.color}]} key={item.id}>
                            <View>
                                <Text style={{textAlign:'center'}}>0</Text>
                                <Text style={{textAlign:'center', textTransform:'uppercase'}}>{item.name}</Text>
                            </View>
                        </View>

                        );
                    })}
                </View>  
                <ScrollView>
                    {ordersList.map(item=>{
                        return(
                            <OrdersCard key={item.order_id} item={item} />
                        );

                    })}
                </ScrollView>     
            </View>
         
        </SafeAreaView>
    );


}