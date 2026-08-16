import AddButton from "./AddButton";

function PageHeader({
    title,
    buttonText,
}: {
    title: string;
    buttonText: string;
}) {
    return (
        <header>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <h1 className="text-2xl font-bold text-gray-900 md:text-4xl">
                    {title}
                </h1>

                <AddButton val={buttonText} />
            </div>
        </header>
    );
}

export default PageHeader;
