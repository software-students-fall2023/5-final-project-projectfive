import { Link } from "react-router-dom";
import logo from '../img/logo.svg';
import '../App.css';

function Home() {
    return ( 
      <div id="home" className="container">
          <h1 id="title">todo</h1>
          <div>
          <img src={logo} alt="home icon" id="hp"></img>
          </div>
          <form>
            <Link className="btn" to="/Login"> 
            <input id="Login" class="Login" type="submit" value="Login"/> 
            </Link>
            <Link to="/Signup">
            <input id="Singup" class="Signup" type="submit" value="Signup"/> 
            </Link> 
          </form>
      </div>
    );
  }
  
  export default Home;