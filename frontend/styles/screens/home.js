import { StyleSheet } from 'react-native';

const home = StyleSheet.create({
 container: {
    flex: 1,
    backgroundColor: '#FFF8E7',
  },
  searchAndFilter:{
    display:'flex',
    flexDirection:'row',
    gap:5,
    
  },
  filterBtn:{
    flex:1,
    backgroundColor:'#FFFFFF',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 3,
      borderRadius:2,
      padding:'5%',
      boxShadow: '3px 3px rgba(0, 0, 0, 1)',
      outlineStyle: 'none',
      display:'flex',
      justifyContent:'center',
      alignItems:'center',

  },
  itemsList:{
   
  },
  itemListCard:{
      backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 3,
      borderRadius:2,
      boxShadow: '5px 5px rgba(0, 0, 0, 1)',
      outlineStyle: 'none',
      marginBottom:10,
      marginEnd:4,
      position:'relative',
      userSelect:'none',
      
     

  },
  cardButtonsView:{
    display:'flex',
    flexDirection:'row',
    borderTopWidth:2,
  },
  cardButton:{
    
    display:'flex',
    flexDirection:'row',
    justifyContent:'center',
    flex:1,
    padding:'2%',
    

  }, 
  addToCartView:{
    borderTopWidth:2,
    flex:1,
    display:'flex',
    flexDirection:'row',
    justifyContent:'center',
  },
  cardCountBtn:{
    display:'flex',
    flexDirection:'row',
    justifyContent:'center',
    borderLeftWidth:2,
    flex:1,
    padding:'2%',
  },
  cardCountDisplays:{




  },
  cardCountDisplay:{
    backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 2,
      borderRadius:2,
      width:'fit-content',
      paddingInline:'3%',
      boxShadow: '1px 2px rgba(0, 0, 0)',
      position:'absolute',
      right:10,
      top:10,
      zIndex:2,

  },
  itemOverview:{
    marginTop:5,
    position:'absolute',
    // borderWidth:2,
    
    width:'70%',
    height:'80%',
    zIndex:2,
    padding:10,
    gap:6,
    display:'flex',
    experimental_backgroundImage:
    'linear-gradient(to right, rgb(191, 190, 190), rgba(0,0,0,0))',
    


    
  },
  itemName:{
    color:'white',
    fontWeight:900,
    fontSize:30
  },
  itemPrice:{
    color:'white',
    fontSize:30,
  },
  veg: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderRadius: 2,
    alignSelf: 'flex-start',
    paddingVertical: 4,
    paddingHorizontal: 8,

    flexDirection: 'row',
    alignItems: 'center',
},
overlay:{

  position:'absolute',
  backgroundColor: 'rgba(158, 157, 157, 0.5)',
  zIndex:1,
  top:0,
  bottom:0,
  right:0,
  left:0,
  display:'flex',
  justifyContent:'center',
  alignItems:'center',


},
popupForm:{
  backgroundColor:'white',
  padding:'5%',
  borderWidth:3,
  display:'flex',
  flexDirection:'column',
  gap:8,
  
  
},

itemsGrouping:{
  display:'flex',
  flexDirection:'row',
  display:'flex',
  flexWrap:'wrap',
  gap:2,

},
filterPrefBtn:{
  backgroundColor:'white',
  borderWidth:2,
  padding:5

},
goToCartBtn:{
    backgroundColor:'#B8F23D',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 3,
      borderRadius:2,
      padding:'5%',
      boxShadow: '3px 3px rgba(0, 0, 0, 1)',
      outlineStyle: 'none',
      display:'flex',
      justifyContent:'center',
      alignItems:'center',

},
detailsCard: {
  width: '85%',
  gap: 10,
},
detailsTitle: {
  fontWeight: '900',
  fontSize: 24,
},
detailsPrice: {
  fontSize: 20,
  fontWeight: 'bold',
},
statusCards:{
  display:'flex',
  flexDirection:'row',
  gap:10,
},
statusCard:{
  flex:1,
  borderWidth:2,
  boxShadow: '4px 5px rgba(0, 0, 0)',
  padding:5,
  display:'flex',
  flexDirection:'row',
  justifyContent:'center'
},
ordersCard:{

  borderWidth:2,
  backgroundColor:'white',
  boxShadow: '4px 5px rgba(0, 0, 0)',
  marginBottom:10,
  padding:5,


}




});

export default home;