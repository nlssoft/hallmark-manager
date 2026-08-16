import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LayoutDashboard } from "lucide-react";
import type { option } from "../types/frontedTypes/navbar";
import { useState } from "react";
import { ProfileMenu } from "./ProfileMenu";
import { User, CreditCard, Settings, KeyRound } from "lucide-react";
import { useEffect, useRef } from "react";
import useRouting from "../hooks/useRouting";

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
    },
];

function NavBar() {
    const { user, logoutUser } = useAuth();
    const appName = import.meta.env.VITE_WEBSITE_NAME;
    const nav = useRouting();
    const [open, setOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    const letter = user?.username?.[0]?.toUpperCase() ?? "?";

    useEffect(() => {
        function handleClick(event: MouseEvent) {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target as Node)
            ) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClick);

        return () => {
            document.removeEventListener("mousedown", handleClick);
        };
    }, []);

    return (
        <div className="sticky top-0 z-50 flex justify-between border-b border-stone-200 bg-white/80 py-4 backdrop-blur-md">
            <button
                onClick={() => nav.dashboard()}
                className="flex cursor-pointer items-center"
            >
                <LayoutDashboard className="ml-3" />
                <div className="ml-1 text-xl font-semibold tracking-tight text-stone-900">
                    {appName}
                </div>
            </button>

            <div ref={menuRef}>
                <button
                    onClick={() => setOpen((prev) => !prev)}
                    className="mr-5 flex h-10 w-10 cursor-pointer items-center justify-center rounded-full bg-stone-200 font-semibold text-stone-700 transition-all hover:bg-stone-300"
                >
                    {letter}
                </button>

                {open && (
                    <ProfileMenu
                        user={user!}
                        options={options}
                        fn={nav.go}
                        logoutFn={logoutUser}
                    />
                )}
            </div>
        </div>
    );
}

export default NavBar;
