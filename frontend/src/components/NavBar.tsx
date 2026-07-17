import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LayoutDashboard } from "lucide-react";


function NavBar(){
    const {user} = useAuth();
    const appName = import.meta.env.VITE_WEBSITE_NAME
    const navigate = useNavigate();

    const letter= user?.username?.[0]?.toUpperCase() ?? "?";



    function handleRouting() {
        navigate("/dashboard");
    }

    return(
        <div className="flex justify-between py-4 
            sticky top-0 z-50
            border-b border-stone-200 bg-white/80 backdrop-blur-md">
            
            <button onClick={handleRouting} className="flex">
                <LayoutDashboard className="ml-3"/>
                <div 
                    className="ml-1 font-semibold text-stone-900 
                    text-xl tracking-tight">{appName}
                </div>
            </button>


            <button className="flex items-center 
                justify-center w-10 h-10 rounded-full 
                bg-stone-200 text-stone-700 font-semibold
                hover:bg-stone-300
                transition-all">

                    {letter}
            </button>

        </div>
    );                                                            
}

export default NavBar;