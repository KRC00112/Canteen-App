import { Alert, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useCallback, useEffect, useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import styles from '../../styles';
import home from '../../styles/screens/home';
import { AdminFoodCard } from '../../components/AdminDataCard';

const API_URL = 'https://canteen-backend-xzko.onrender.com';

const EMPTY_FORM = {
  name: '',
  price: '',
  description: '',
  category: '',
  food_type: 'VEG',
  ingredients: '',
  avg_cooking_time_minutes: '10',
};

function FoodItemForm({ item, token, onSaved, onClose }) {
  const [form, setForm] = useState(item ? {
    name: item.name ?? '',
    price: String(item.price ?? ''),
    description: item.description ?? '',
    category: item.category ?? '',
    food_type: item.food_type ?? 'VEG',
    ingredients: (item.ingredients ?? []).join(', '),
    avg_cooking_time_minutes: String(item.avg_cooking_time_minutes ?? 10),
  } : EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  function updateField(field, value) {
    setForm(current => ({ ...current, [field]: value }));
  }

  function validate() {
    if (!form.name.trim() || !form.category.trim()) return 'Name and category are required.';
    if (!Number.isFinite(Number(form.price)) || Number(form.price) <= 0) return 'Price must be greater than zero.';
    const minutes = Number(form.avg_cooking_time_minutes);
    if (!Number.isInteger(minutes) || minutes < 1 || minutes > 180) return 'Cooking time must be between 1 and 180 minutes.';
    return null;
  }

  async function saveItem() {
    const validationError = validate();
    if (validationError) {
      Alert.alert('Check the form', validationError);
      return;
    }

    const payload = {
      name: form.name.trim(),
      price: Number(form.price),
      description: form.description.trim() || null,
      category: form.category.trim(),
      food_type: form.food_type,
      ingredients: form.ingredients.split(',').map(value => value.trim()).filter(Boolean),
      avg_cooking_time_minutes: Number(form.avg_cooking_time_minutes),
    };

    setSaving(true);
    try {
      const response = await fetch(
        item ? `${API_URL}/admin/items/${item.id}` : `${API_URL}/admin/items`,
        {
          method: item ? 'PATCH' : 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        }
      );
      const result = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = typeof result?.detail === 'string' ? result.detail : 'The food item could not be saved.';
        throw new Error(detail);
      }
      onSaved(result);
    } catch (error) {
      Alert.alert('Unable to save item', error.message || 'Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={home.overlay}>
      <View style={[home.popupForm, styles.adminForm]}>
        <ScrollView
          style={styles.adminFormScroll}
          contentContainerStyle={styles.adminFormContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator
        >
          <View style={styles.adminFormHeader}>
            <View>
              <Text style={styles.sectionKicker}>{item ? 'Edit menu item' : 'New menu item'}</Text>
              <Text style={styles.sectionTitle}>{item ? item.name : 'Add food'}</Text>
            </View>
            <Pressable onPress={onClose} style={styles.adminCloseButton}>
              <Ionicons name="close" size={22} color="#111111" />
            </Pressable>
          </View>

          <Text style={styles.formInputLabel}>Name *</Text>
          <TextInput value={form.name} onChangeText={value => updateField('name', value)} style={styles.inputText} placeholder="Paneer wrap" placeholderTextColor="#666666" />
          <Text style={styles.formInputLabel}>Price (INR) *</Text>
          <TextInput value={form.price} onChangeText={value => updateField('price', value)} style={styles.inputText} placeholder="60" placeholderTextColor="#666666" keyboardType="decimal-pad" />
          <Text style={styles.formInputLabel}>Category *</Text>
          <TextInput value={form.category} onChangeText={value => updateField('category', value)} style={styles.inputText} placeholder="Snacks" placeholderTextColor="#666666" />
          <Text style={styles.formInputLabel}>Description</Text>
          <TextInput value={form.description} onChangeText={value => updateField('description', value)} style={[styles.inputText, styles.multilineInput]} placeholder="Short description" placeholderTextColor="#666666" multiline />
          <Text style={styles.formInputLabel}>Food type</Text>
          <View style={styles.formChoiceRow}>
            {['VEG', 'NON_VEG'].map(type => (
              <Pressable key={type} onPress={() => updateField('food_type', type)} style={[styles.formChoice, form.food_type === type && styles.formChoiceSelected]}>
                <Text style={styles.formChoiceText}>{type.replace('_', '-')}</Text>
              </Pressable>
            ))}
          </View>
          <Text style={styles.formInputLabel}>Ingredients (comma separated)</Text>
          <TextInput value={form.ingredients} onChangeText={value => updateField('ingredients', value)} style={styles.inputText} placeholder="Paneer, wrap, onion" placeholderTextColor="#666666" />
          <Text style={styles.formInputLabel}>Cooking time (minutes) *</Text>
          <TextInput value={form.avg_cooking_time_minutes} onChangeText={value => updateField('avg_cooking_time_minutes', value)} style={styles.inputText} placeholder="10" placeholderTextColor="#666666" keyboardType="number-pad" />

          <Text style={styles.formHint}>Stock and availability are managed by canteen staff.</Text>
          <Pressable onPress={saveItem} disabled={saving} style={[styles.button, saving && styles.buttonDisabled]}>
            <Text style={styles.buttonText}>{saving ? 'Saving...' : item ? 'Save changes' : 'Create item'}</Text>
          </Pressable>
        </ScrollView>
      </View>
    </View>
  );
}

export default function FoodItems({ route }) {
  const token = route?.params?.userData?.access_token;
  const [foodList, setFoodList] = useState([]);
  const [formItem, setFormItem] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const getFoodList = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/menu`);
      if (!response.ok) throw new Error('Unable to load food items.');
      setFoodList(await response.json());
    } catch (error) {
      Alert.alert('Unable to load menu', error.message || 'Please try again.');
    }
  }, []);

  useEffect(() => {
    getFoodList();
  }, [getFoodList]);

  function openCreateForm() {
    setFormItem(undefined);
    setShowForm(true);
  }

  function openEditForm(item) {
    setFormItem(item);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setFormItem(null);
  }

  function handleSaved(savedItem) {
    setFoodList(current => {
      const exists = current.some(item => item.id === savedItem.id);
      return exists ? current.map(item => item.id === savedItem.id ? savedItem : item) : [savedItem, ...current];
    });
    closeForm();
  }

  function deleteItem(item) {
    Alert.alert(
      'Delete food item?',
      `"${item.name}" will be removed from the menu. Past orders are not affected.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${API_URL}/admin/items/${item.id}`, {
                method: 'DELETE',
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              });
              const result = await response.json().catch(() => null);
              if (!response.ok) {
                const detail = typeof result?.detail === 'string' ? result.detail : 'The food item could not be deleted.';
                throw new Error(detail);
              }
              setFoodList(current => current.filter(foodItem => foodItem.id !== item.id));
            } catch (error) {
              Alert.alert('Unable to delete item', error.message || 'Please try again.');
            }
          },
        },
      ],
    );
  }

  return (
    <SafeAreaView style={home.container} edges={['top', 'left', 'right']}>
      <View style={styles.defaultView}>
        {showForm && <FoodItemForm item={formItem} token={token} onSaved={handleSaved} onClose={closeForm} />}
        <Pressable onPress={openCreateForm} style={styles.addNewCard}>
          <Ionicons name="add-circle-outline" size={28} color="black" />
          <Text style={{ fontWeight: '900' }}>Add New Food Item</Text>
        </Pressable>
        <ScrollView>
          {foodList.map(item => (
            <AdminFoodCard key={item.id} item={item} onEdit={openEditForm} onDelete={deleteItem} />
          ))}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}
