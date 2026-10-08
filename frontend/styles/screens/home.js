import { StyleSheet } from 'react-native';

const home = StyleSheet.create({
 container: {
    display:'flex',
    flexDirection:'column',
    justifyContent:'flex-start',
    width:'100%',
    height:'100%',
    // backgroundColor:'green',
    
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
   
  },
  itemListCard:{
    // backgroundColor:'red',
      backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 2,
      borderRadius:2,
      boxShadow: '4px 5px rgba(0, 0, 0)',
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
  cardCountDisplay:{
    backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 2,
      borderRadius:2,
      width:'fit-content',
      paddingInline:'3%',
      position:'absolute',
      zIndex:2,
      right:10,
      top:10,
      boxShadow: '1px 2px rgba(0, 0, 0)',

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

filterForm:{
  backgroundColor:'red',
  padding:'5%',
  
},

itemsGrouping:{
  display:'flex',
  flexDirection:'row',
  display:'flex',
  flexWrap:'wrap'

},
filterPrefBtn:{
  backgroundColor:'white',
  borderWidth:2,

}
});

export default home;