import { StyleSheet } from 'react-native';

const home = StyleSheet.create({
 container: {
    display:'flex',
    flexDirection:'column',
    justifyContent:'flex-start',
    width:'100%',
    height:'100%',
    
  },
  searchAndFilter:{
    display:'flex',
    flexDirection:'row',
    gap:5,
    
  },
  filterBtn:{
    flex:1,
    backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 2,
      borderRadius:2,
      padding:'5%',
      boxShadow: '4px 5px rgba(0, 0, 0)',
      outlineStyle: 'none',
  },
  itemsList:{
    flex:1,
  },
  itemListCard:{
    backgroundColor:'red',

  }
});

export default home;