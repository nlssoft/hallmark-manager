import type { option, ProfileMenuProps } from "../types/frontedTypes/navbar";
import { LogOut  } from "lucide-react";


export function ProfileMenu({options, user, fn, logoutFn}: ProfileMenuProps){

    if (!user.isParent){
        options= options.filter((o)=> !o.parentOnly)
    }
    
    return(
        <div className=" grid absolute 
        right-1 top-16 w-60 border rounded-xl
        bg-white border-gray-200 shadow-xl 
        ">
            <div className="flex flex-col items-center 
            bg-gray-50 border border-transparent
            rounded-md p-2 mt-2">

                <h1 className="text-gray-900 font-semibold">
                    {user.username}
                </h1>
                <p className="text-gray-500 font-sm leading-relaxed">
                    {user.email}
                </p>
            </div>

            <div className="grid items-center">
            {
                options.map((o:option)=>{
                    const Icon = o.icon
                  
                    return (
                        <button 
                        key={o.key} 
                        onClick={()=>fn(o.route)}
                        className="flex items-center gap-3 w-full px-3 py-2 
                        text-sm text-gray-700 rounded-md
                        hover:bg-gray-100 hover:text-gray-900 cursor-pointer">
                        
                        <Icon className="text-gray-500"/>
                            {o.name}
                        </button>
                    );
                })
            }
            </div>

            
            <button onClick={()=>logoutFn()} className="flex items-center gap-3 w-full
            cursor-pointer text-sm text-red-600 
            rounded-md hover:bg-red-50 px-3 py-2 ">
                <LogOut className="text-red-400"/>
                Logout
           </button>

        </div>

    );
}