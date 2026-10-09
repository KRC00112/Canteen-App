import { useState,createContext } from 'react';
export const AddItemContext=() => {
    const [cartItems, setCartItems]=useState([]);

    createContext(
        function addingItemsToCart(id) {
        setCartItems(prev => {
            const existingItem = prev.find(item => item.id === id);

            if (existingItem) {
                return prev.map(item =>
                    item.id===id?{...item, count: item.count+1}:item
                );
            }
            return [...prev, { id, count: 1 }];
        });
    }
)};