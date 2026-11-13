<!DOCTYPE html>
<html>
    <head>  <title>php</title>
      <body>
          
        <input type="button" value="setcookie" onclick="setcookie()">
         <input type="button" value="getcookie" onclick="getcookie()">
         <script type="text/javascript">
          function setcookie(){
            document.cookie="companyname=learnvern";
          }
          function getcookie(){
            if(document.cookie.length !=0){
              alert("document.cookie");

            }
            else{
              alert("cookie is not set");
            }
          }
          
         </script>

    </body>
</html>