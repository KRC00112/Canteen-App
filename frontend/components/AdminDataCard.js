import { Pressable, Text, View } from 'react-native';
import styles from '../styles';

function Meta({ label, value }) {
  return (
    <View style={styles.adminMeta}>
      <Text style={styles.adminMetaLabel}>{label}</Text>
      <Text style={styles.adminMetaValue}>{value ?? '-'}</Text>
    </View>
  );
}

function formatDate(value) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString();
}

export function AdminUserCard({ user }) {
  return (
    <View style={styles.adminCard}>
      <View style={styles.adminCardHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.adminCardTitle}>{user.username}</Text>
          <Text style={styles.adminCardSubtitle}>User #{user.id} · {user.institute_id}</Text>
        </View>
        <View style={[styles.adminBadge, { backgroundColor: user.is_logged_in ? '#B8F23D' : '#FFD43B' }]}>
          <Text style={styles.adminBadgeText}>{user.is_logged_in ? 'Online' : user.account_status}</Text>
        </View>
      </View>
      <View style={styles.adminMetaGrid}>
        <Meta label="Role" value={user.role} />
        <Meta label="Account" value={user.account_status} />
        <Meta label="Active sessions" value={user.active_sessions} />
        <Meta label="Total logins" value={user.total_logins} />
        <Meta label="Last login" value={formatDate(user.last_login_at)} />
        <Meta label="Joined" value={formatDate(user.created_at)} />
      </View>
    </View>
  );
}

export function AdminFoodCard({ item, onEdit, onDelete }) {
  return (
    <View style={styles.adminCard}>
      <View style={styles.adminCardHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.adminCardTitle}>{item.name}</Text>
          <Text style={styles.adminCardSubtitle}>Item #{item.id} · {item.category}</Text>
        </View>
        <View style={[styles.adminBadge, { backgroundColor: item.available ? '#B8F23D' : '#FF8066' }]}>
          <Text style={styles.adminBadgeText}>{item.available ? 'Available' : 'Unavailable'}</Text>
        </View>
      </View>
      {!!item.description && <Text style={{ marginTop: 10, color: '#444' }}>{item.description}</Text>}
      <View style={styles.adminMetaGrid}>
        <Meta label="Price" value={`₹ ${item.price}`} />
        <Meta label="Type" value={item.food_type} />
        <Meta label="Stock" value={item.stock_status} />
        <Meta label="Cook time" value={`${item.avg_cooking_time_minutes} min`} />
        <Meta label="Max order" value={item.max_order_quantity} />
        <Meta label="Popularity" value={item.popular ? 'Popular today' : 'Regular item'} />
      </View>
      {/* {!!item.stock_message && <Text style={{ marginTop: 10, fontWeight: '800' }}>{item.stock_message}</Text>} */}
      <View style={{display:'flex', flexDirection:'row', gap:8}}>
          <Pressable
          onPress={() => onEdit(item)}
          style={{
            backgroundColor: '#7048E8',
            borderWidth: 3,
            borderColor: '#111111',
            padding: 12,
            marginTop: 8,
            alignItems: 'center',
            flex:1,
          }}
        >
          <Text style={{ color: '#FFFFFF', fontWeight: '900', textTransform: 'uppercase' }}>Edit item</Text>
        </Pressable>
        <Pressable
          onPress={() => onDelete(item)}
          style={{
            backgroundColor: '#FF8066',
            borderWidth: 3,
            borderColor: '#111111',
            padding: 12,
            marginTop: 8,
            alignItems: 'center',
            flex:1,
          }}
        >
          <Text style={{ color: '#111111', fontWeight: '900', textTransform: 'uppercase' }}>Delete item</Text>
        </Pressable>
      </View>

    </View>
  );
}
