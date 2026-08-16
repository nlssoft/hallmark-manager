import { Plus } from "lucide-react";

function AddButton({ val }: { val: string }) {
    return (
        <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-black px-4 py-3 text-sm text-white shadow-md hover:shadow-lg sm:w-auto sm:px-5">
            <Plus className="h-5 w-5 shrink-0" />
            Add {val}
        </button>
    );
}

export default AddButton;
