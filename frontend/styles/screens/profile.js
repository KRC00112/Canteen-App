import { StyleSheet } from 'react-native';

const profile = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
    backgroundColor: '#FFF8E7',
  },
  heading: {
    fontSize: 28,
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
  headerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
  },
  avatar: {
    width: 64,
    height: 64,
    borderWidth: 2,
    borderRadius: 2,
    backgroundColor: '#FFD966',
    justifyContent: 'center',
    alignItems: 'center',
    boxShadow: '2px 3px rgba(0, 0, 0)',
  },
  avatarText: {
    fontSize: 30,
    fontWeight: '900',
  },
  username: {
    fontSize: 22,
    fontWeight: '900',
  },
  badge: {
    alignSelf: 'flex-start',
    borderWidth: 2,
    borderRadius: 2,
    paddingVertical: 2,
    paddingHorizontal: 8,
    marginTop: 4,
    backgroundColor: '#9FC5E8',
    boxShadow: '1px 2px rgba(0, 0, 0)',
  },
  badgeText: {
    fontWeight: 'bold',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
  },
  rowBorder: {
    borderTopWidth: 2,
  },
  label: {
    color: '#555',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  value: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  empty: {
    textAlign: 'center',
    marginTop: 40,
    fontSize: 16,
  },
});

export default profile;