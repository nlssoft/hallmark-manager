

function Avatar({logo}: {logo: string}){
    
    return (
        <div className="w-9 h-8 rounded-2xl bg-blue-100 text-blue-700 flex 
        items-center justify-center ">
            {logo}
        </div>
    )
}


export default Avatar