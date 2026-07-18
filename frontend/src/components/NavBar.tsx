import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LayoutDashboard } from "lucide-react";
import type { option } from "../types/frontedTypes/navbar";
import { useState } from "react";
import { ProfileMenu } from "./ProfileMenu";
import { User, CreditCard, Settings, KeyRound  } from "lucide-react";
import { useEffect, useRef } from "react";



const options: option[] = [
    {
        key: "profile",
        name: "Profile",
        route: "/profile",
        parentOnly: false,
        icon: User,
    },
    {
        key: "subscription",
        name: "Subscription",
        route: "/subscription",
        parentOnly: true,
        icon: CreditCard,
    },
    {
        key: "settings",
        name: "Settings",
        route: "/setting",
        parentOnly: true,
        icon: Settings,
    },
    {
        key: "changePassword",
        name: "Change Password",
        route: "/change-password",
        parentOnly: false,
        icon: KeyRound,
    }
]


function NavBar(){
    const {user, logoutUser} = useAuth();
    const appName = import.meta.env.VITE_WEBSITE_NAME
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    const letter= user?.username?.[0]?.toUpperCase() ?? "?";



    function handleRouting(route: string = "/dahsboard") {
        navigate(route);
    }

    useEffect(()=>{
        function handleClick(event:MouseEvent){
            if (menuRef.current && 
                !menuRef.current.contains(event.target as Node)
            ){
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClick);

        return ()=> {
            document.removeEventListener("mousedown", handleClick)
        };

    }, []);


    return(
        <div className="flex justify-between py-4 
            sticky top-0 z-50
            border-b border-stone-200 bg-white/80 backdrop-blur-md">
            
            <button onClick={()=>handleRouting()} className="flex  cursor-pointer">
                <LayoutDashboard className="ml-3"/>
                <div 
                    className="ml-1 font-semibold text-stone-900 
                    text-xl tracking-tight ">{appName}
                </div>
            </button>

            <div ref={menuRef}>
                <button onClick={()=>setOpen(prev=> !prev)} className="flex items-center 
                    justify-center w-10 h-10 rounded-full 
                    bg-stone-200 text-stone-700 font-semibold
                    hover:bg-stone-300
                    transition-all cursor-pointer">

                        {letter}
                </button>

                {open && (
                        <ProfileMenu user={user!} options={options} fn={handleRouting} logoutFn={logoutUser}/>
                )}
            </div>

        </div>
    );                                                            
}

export default NavBar;