import { StyleSheet } from 'react-native';

const register = StyleSheet.create({
 container: {
    display:'flex',
    flexDirection:'column',
    justifyContent:'center',
    alignItems:'center',
    width:'100%',
    height:'100%',
  },
  confirmPasswordLabels:{
    display: 'flex',
    flexDirection: 'row',
    justifyContent:'space-between'
  },
  confirmPasswordMismatchLabels:{
    color:'red',
  },
   inputTextMismatch: {
      color:'red',
      borderColor: 'red',
      boxShadow: '4px 5px rgba(255, 0, 0)',

  }
});

export default register;