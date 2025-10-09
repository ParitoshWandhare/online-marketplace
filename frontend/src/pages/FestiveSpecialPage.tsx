// src/pages/FestiveSpecialPage.tsx
import { useState, useEffect } from "react";
import { ItemCard } from "@/components/ui/ItemCard";
import { Loader } from "@/components/ui/Loader";
import { artworkService, type Artwork } from "@/services/artwork";
import { likeService } from "@/services/like";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

// Festival data for each month
const FESTIVALS: { [key: number]: { tags: string[]; banner: string; color: string } } = {
  1: { tags: ["newyear", "celebration", "gift"], banner: "🎉 Happy New Year!", color: "bg-blue-100" },
  2: { tags: ["valentine", "love", "gift"], banner: "💖 Happy Valentine's Month!", color: "bg-pink-100" },
  3: { tags: ["holi", "colors", "festival"], banner: "🌈 Happy Holi!", color: "bg-purple-100" },
  4: { tags: ["spring", "flowers", "eid"], banner: "🌙 Eid & Spring Specials!", color: "bg-green-100" },
  5: { tags: ["motherday", "gift", "flowers"], banner: "💐 Celebrate Mother’s Month!", color: "bg-yellow-100" },
  6: { tags: ["summer", "beach", "vacation"], banner: "☀️ Summer Specials!", color: "bg-orange-100" },
  7: { tags: ["independenceday", "patriotic", "gift"], banner: "🇮🇳 Independence Month Specials!", color: "bg-red-100" },
  8: { tags: ["friendship", "gift", "celebration"], banner: "🤝 Friendship Month Specials!", color: "bg-green-200" },
  9: { tags: ["diwali", "lights", "gift"], banner: "🪔 Happy Diwali Month!", color: "bg-yellow-100" },
  10: { tags: ["diwali", "lights", "gift"], banner: "🪔 Happy Diwali Month!", color: "bg-yellow-100" },
  11: { tags: ["thanksgiving", "harvest", "gift"], banner: "🦃 Thanksgiving Specials!", color: "bg-orange-200" },
  12: { tags: ["christmas", "xmas", "tree", "gift"], banner: "🎄 Merry Christmas Month!", color: "bg-red-100" },
};

const FestiveSpecialPage: React.FC = () => {
  const { user } = useAuth();
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [likedArtworks, setLikedArtworks] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const currentMonth = new Date().getMonth() + 1; // JS months are 0-indexed
  const festival = FESTIVALS[currentMonth];

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch all published artworks
        const allArtworksResponse = await artworkService.getAllArtworks();
        const allArtworks = allArtworksResponse.artworks || [];

        // Filter artworks by festival tags
        const filteredArtworks = allArtworks.filter(
          (art: Artwork) =>
            Array.isArray(art.tags) &&
            art.tags.some(tag => festival.tags.includes(tag.toLowerCase()))
        );
        setArtworks(filteredArtworks);

        // Fetch liked artworks if user exists
        if (user) {
          const likedResponse = await likeService.getLikedArtworks();
          const likedIds = new Set(likedResponse.artworks.map((art: Artwork) => art._id));
          setLikedArtworks(likedIds);
        }
      } catch (err) {
        console.error("Error fetching artworks:", err);
        toast.error("Failed to load festive items.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, festival]);

  const handleLike = (itemId: string) => {
    setLikedArtworks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const handleWishlist = (itemId: string) => {
    handleLike(itemId);
  };

  if (loading) return <Loader text="Loading festive items..." />;

  if (!festival || artworks.length === 0)
    return <div className="text-center p-8">No festive items available this month 😢</div>;

  return (
    <div className={`min-h-screen p-6 ${festival.color} transition-colors duration-500`}>
      {/* Festival Banner */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold animate-pulse">{festival.banner}</h1>
        <p className="text-gray-700 mt-2">Check out our special items for this festival!</p>
      </div>

      {/* Items Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {artworks.map((artwork) => (
          <ItemCard
            key={artwork._id}
            item={artwork}
            onLike={handleLike}
            onWishlist={handleWishlist}
            isLiked={likedArtworks.has(artwork._id)}
          />
        ))}
      </div>
    </div>
  );
};

export default FestiveSpecialPage;

// src/pages/FestiveSpecialPage.tsx
// import React from "react";

// interface Media {
//   url: string;
//   type: "image" | "video";
// }

// interface Artwork {
//   _id: string;
//   title: string;
//   description: string;
//   price: number;
//   currency: string;
//   quantity: number;
//   media: Media[];
//   tags: string[];
// }

// // Mock data for Diwali festival
// const mockArtworks: Artwork[] = [
//   {
//     _id: "1",
//     title: "Traditional Diya Set",
//     description: "A beautiful handcrafted Diya set to light up your Diwali nights.",
//     price: 499,
//     currency: "INR",
//     quantity: 20,
//     media: [
//       { url: "https://static.toiimg.com/thumb/msid-114768822,width-400,resizemode-4/114768822.jpg", type: "image" }
//     ],
//     tags: ["diwali", "lights", "gift"]
//   },
//   {
//     _id: "2",
//     title: "Rangoli Powder Colors",
//     description: "Vibrant and safe Rangoli colors to decorate your home for Diwali.",
//     price: 299,
//     currency: "INR",
//     quantity: 50,
//     media: [
//       { url: "https://5.imimg.com/data5/SELLER/Default/2024/9/452491422/NW/ZX/BJ/930138/festival-rangoli-powder-500x500.png", type: "image" }
//     ],
//     tags: ["diwali", "colors", "decoration"]
//   },
//   {
//     _id: "3",
//     title: "Diwali Gift Hamper",
//     description: "A festive gift hamper with sweets, dry fruits, and decor items.",
//     price: 1499,
//     currency: "INR",
//     quantity: 10,
//     media: [
//       { url: "data:image/jpeg;base64,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", type: "image" }
//     ],
//     tags: ["diwali", "gift", "sweets"]
//   },
//   {
//     _id: "4",
//     title: "LED String Lights",
//     description: "Decorate your home with colorful LED lights for Diwali celebrations.",
//     price: 799,
//     currency: "INR",
//     quantity: 30,
//     media: [
//       { url: "https://m.media-amazon.com/images/I/71YVojIUZRL._UF1000,1000_QL80_.jpg", type: "image" }
//     ],
//     tags: ["diwali", "lights", "decoration"]
//   }
// ];

// const FestiveSpecialPage: React.FC = () => {
//   return (
//     <div className="min-h-screen bg-yellow-50 p-6">
//       {/* Festival Banner */}
//       <div className="text-center mb-8">
//         <h1 className="text-5xl font-bold text-orange-500 animate-pulse">
//           🪔 Happy Diwali!
//         </h1>
//         <p className="text-gray-700 mt-2 text-lg">
//           Celebrate the festival of lights with our special Diwali items!
//         </p>
//       </div>

//       {/* Items Grid */}
//       <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
//         {mockArtworks.map((item) => (
//           <div
//             key={item._id}
//             className="bg-white rounded-lg shadow-lg overflow-hidden transform transition hover:scale-105 hover:shadow-2xl"
//           >
//             <div className="relative h-56 w-full overflow-hidden">
//               <img
//                 src={item.media[0]?.url}
//                 alt={item.title}
//                 className="w-full h-full object-cover"
//               />
//               <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm font-semibold">
//                 {item.currency} {item.price}
//               </div>
//             </div>
//             <div className="p-4">
//               <h2 className="font-bold text-lg mb-1">{item.title}</h2>
//               <p className="text-sm text-gray-600 line-clamp-3 mb-2">{item.description}</p>
//               <div className="flex flex-wrap gap-2 mt-2">
//                 {item.tags.map((tag) => (
//                   <span key={tag} className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs">
//                     #{tag}
//                   </span>
//                 ))}
//               </div>
//             </div>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// };

// export default FestiveSpecialPage;
