import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    display:'flex',
    flexDirection:'column',
    justifyContent:'center',
    alignItems:'center',
    width:'100%',
    height:'100%',
  },
  header: {
      color:'purple',
      textTransform:'uppercase',
      fontWeight:'900',
      fontSize: 50,
      
  },
    inputText: {
      backgroundColor:'white',
      borderColor: 'black',
      borderStyle:'solid',
      borderWidth: 2,
      borderRadius:2,
      padding:'5%',
      boxShadow: '4px 5px rgba(0, 0, 0)',
      outlineStyle: 'none',
  },
  formInputComponent:{
    marginTop:'5%',
    gap:'3%',
  },
  form: {
    display:'flex',
    justifyContent: 'center',
    width:'70%',
  },
  button: {
    backgroundColor: 'purple',
    height:'fit-content',
    width:'100%',
    borderColor: 'black',
    borderStyle:'solid',
    borderWidth: 2,
    borderRadius:30,
    padding:'5%',
    boxShadow: '3px 4px rgba(0, 0, 0)',
    display:'flex',
    flexDirection:'row',
    justifyContent:'center',
    marginTop:'10%',
    
  },
  buttonText: {
    color:'white',
    fontWeight:'900',
    fontSize: 15,
    textTransform: 'uppercase',
  },accountAvailabilityMessage:{
    marginTop:'8%',
    alignSelf:'center',
    cursor:'pointer',
    fontSize:15,
    fontWeight:500
  },
  link:{
    color: 'purple',
    fontWeight:700,
  },
  formInputLabel:{
    fontWeight:500
  },
  searchInput:{
    borderRadius:30,
    padding:'5%',
    outlineStyle:'none',
    backgroundColor: 'rgb(228, 224, 224)',
    textAlign:'center'
  },
  defaultView:{
    padding:'5%',
    flex: 1,
    gap:10
  },
  appBar:{
    padding:'2%'
  }
});

export default styles;