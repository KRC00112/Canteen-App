// styles/orders.js
import { StyleSheet } from 'react-native';

const orders = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF8E7',
  },
  heading: {
    fontSize: 30,
    fontWeight: '900',
    marginBottom: 12,
  },
  card: {
    backgroundColor: 'white',
    borderColor: 'black',
    borderStyle: 'solid',
    borderWidth: 3,
    borderRadius: 2,
    boxShadow: '5px 5px rgba(0, 0, 0, 1)',
    marginBottom: 14,
    marginEnd: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 10,
    borderBottomWidth: 2,
  },
  orderId: {
    fontWeight: '900',
    fontSize: 18,
  },
  statusBadge: {
    borderWidth: 2,
    borderRadius: 2,
    paddingVertical: 2,
    paddingHorizontal: 8,
    boxShadow: '1px 2px rgba(0, 0, 0)',
  },
  statusText: {
    fontWeight: 'bold',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  cardBody: {
    padding: 10,
    gap: 4,
  },
  label: {
    color: '#555',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  value: {
    fontSize: 16,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 10,
    borderTopWidth: 2,
  },
  totalText: {
    fontWeight: '900',
    fontSize: 22,
  },
  empty: {
    textAlign: 'center',
    marginTop: 40,
    fontSize: 16,
  },
});

export default orders;