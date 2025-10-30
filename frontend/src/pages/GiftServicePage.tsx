// src/pages/GiftServicePage.tsx
import { useState } from "react";
import {
  giftAiService,
  GiftBundle,
  GenerateBundleResponse,
  SearchResponse,
} from "@/services/giftAi";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import {
  Loader2,
  Upload,
  Search,
  Sparkles,
  Image as ImageIcon,
  IndianRupee,
  AlertCircle,
  Info,
} from "lucide-react";

export default function GiftServicePage() {
  // -----------------------------------------------------------------------
  // STATE
  // -----------------------------------------------------------------------
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const [bundleResult, setBundleResult] = useState<GenerateBundleResponse | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);

  const [error, setError] = useState("");

  // -----------------------------------------------------------------------
  // IMAGE UPLOAD
  // -----------------------------------------------------------------------
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please upload a valid image file (JPG, PNG, etc.)");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Image size must be less than 5 MB");
      return;
    }

    setImageFile(file);
    setError("");
    console.log("Image uploaded:", file.name);
  };

  // -----------------------------------------------------------------------
  // BUNDLE GENERATION
  // -----------------------------------------------------------------------
  const generateBundle = async () => {
    if (!imageFile) {
      setError("Please upload an image first");
      return;
    }

    setLoading(true);
    setError("");
    setBundleResult(null);

    try {
      console.log("Generating bundle from image…");
      const res = await giftAiService.generateGiftBundle(imageFile);
      console.log("Bundle result:", res);

      if (!res.success) {
        setError(res.message || "Bundle generation failed");
        return;
      }

      if (!res.bundles || res.bundles.length === 0) {
        setError("No bundles generated. Please try a different image.");
        return;
      }

      // Set the result - this should trigger re-render
      setBundleResult(res);
      console.log("✅ Bundle result set successfully, count:", res.bundles.length);
    } catch (e: any) {
      console.error("Bundle error:", e);
      setError(e.message || "Failed to generate bundle");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------------------------------------
  // TEXT SEARCH
  // -----------------------------------------------------------------------
  const searchGifts = async () => {
    const q = searchQuery.trim();
    if (!q) return setError("Enter a search query");

    setLoading(true);
    setError("");
    setSearchResult(null);

    try {
      console.log("Searching gifts for:", q);
      const res = await giftAiService.searchSimilarGifts(q, 12);
      console.log("Search result:", res);

      if (!res.success || !res.bundles?.length) {
        setError(`No results for "${q}"`);
        return;
      }
      setSearchResult(res);
    } catch (e: any) {
      console.error("Search error:", e);
      setError(e.message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------------------------------------
  // BUNDLE CARD RENDERER (image-based bundles)
  // -----------------------------------------------------------------------
  const renderBundleCard = (bundle: GiftBundle, idx: number) => (
    <Card key={bundle.bundle_id || idx} className="p-6 shadow-lg border-purple-100 bg-gradient-to-br from-purple-50 to-pink-50">
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-purple-800 mb-2">
          {bundle.bundle_name || bundle.name || `Bundle ${idx + 1}`}
        </h3>
        {bundle.description && <p className="text-sm text-gray-700">{bundle.description}</p>}
        {bundle.theme && <Badge variant="secondary" className="mt-2">{bundle.theme}</Badge>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {bundle.items?.map((item, i) => {
          const artwork = item.artwork;
          const id = item.mongo_id || artwork._id;
          const title = artwork.title || item.title;
          const price = artwork.price ?? item.price;
          const img = artwork.media?.[0]?.url;
          const reason = item.reason;

          return (
            <div key={id || `${idx}-${i}`} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow">
              <div className="h-48 bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                {img ? (
                  <img src={img} alt={title} className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="w-16 h-16 text-purple-300" />
                )}
              </div>
              <div className="p-4 space-y-3">
                <h4 className="font-semibold text-sm line-clamp-2">{title}</h4>
                <p className="text-xs text-gray-600 line-clamp-3">{reason}</p>
                {item.similarity !== undefined && (
                  <Badge variant="outline" className="text-xs">
                    {(item.similarity * 100).toFixed(0)}% match
                  </Badge>
                )}
                <div className="flex justify-between items-center pt-2 border-t">
                  <p className="text-purple-600 font-bold text-sm flex items-center">
                    <IndianRupee className="w-3 h-3 mr-1" />
                    {typeof price === "number" ? price.toLocaleString("en-IN") : price}
                  </p>
                  <Link to={`/artwork/${id}`} className="text-xs text-purple-600 hover:underline">
                    View Details
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-purple-200 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold">Bundle Total:</span>
          <Badge variant="outline" className="text-xs">
            {bundle.item_count} {bundle.item_count === 1 ? 'item' : 'items'}
          </Badge>
        </div>
        <span className="text-2xl font-bold text-purple-600 flex items-center">
          <IndianRupee className="w-5 h-5 mr-1" />
          {bundle.total_price.toLocaleString("en-IN")}
        </span>
      </div>
    </Card>
  );

  // -----------------------------------------------------------------------
  // MAIN RENDER
  // -----------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center justify-center gap-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            Gift AI Studio
          </h1>
          <p className="text-lg text-gray-600">
            Upload an image or search to discover perfect gifts powered by AI
          </p>
        </div>

        {/* Global Error */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Tabs */}
        <Tabs defaultValue="bundle" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="bundle">Generate Bundle</TabsTrigger>
            <TabsTrigger value="search">Text Search</TabsTrigger>
          </TabsList>

          {/* ---------- BUNDLE TAB ---------- */}
          <TabsContent value="bundle">
            <Card className="p-6">
              <div className="space-y-6">
                {/* Upload */}
                <div className="border-2 border-dashed border-purple-300 rounded-xl p-8 text-center hover:border-purple-400 transition-colors">
                  <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" id="bundle-img" />
                  <label htmlFor="bundle-img" className="cursor-pointer block">
                    {imageFile ? (
                      <div className="space-y-3">
                        <img src={URL.createObjectURL(imageFile)} alt="Preview" className="mx-auto h-48 rounded-lg object-contain shadow-md" />
                        <p className="text-sm font-medium">{imageFile.name}</p>
                        <p className="text-xs text-gray-500">Click to change</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <Upload className="mx-auto h-12 w-12 text-purple-500" />
                        <p className="text-lg font-medium">Click to upload image</p>
                        <p className="text-sm text-gray-500">JPG, PNG up to 5 MB</p>
                      </div>
                    )}
                  </label>
                </div>

                <Button onClick={generateBundle} disabled={!imageFile || loading} className="w-full" size="lg">
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Generating…
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      Generate Gift Bundle
                    </>
                  )}
                </Button>

                {bundleResult && bundleResult.success && bundleResult.bundles && bundleResult.bundles.length > 0 && (
                  <div className="space-y-8">
                    <Alert className="bg-green-50 border-green-200">
                      <Sparkles className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        Generated {bundleResult.bundles.length} bundle{bundleResult.bundles.length > 1 ? "s" : ""}!
                        {bundleResult.metadata?.enrichment_stats && (
                          <span className="ml-2 text-sm">
                            ({bundleResult.metadata.enrichment_stats.found_items}/{bundleResult.metadata.enrichment_stats.total_items} items matched)
                          </span>
                        )}
                      </AlertDescription>
                    </Alert>

                    {/* Warnings if present */}
                    {bundleResult.warnings && bundleResult.warnings.length > 0 && (
                      <Alert className="bg-yellow-50 border-yellow-200">
                        <Info className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">
                          <p className="font-semibold mb-1">Processing notes:</p>
                          <ul className="list-disc list-inside text-sm space-y-1">
                            {bundleResult.warnings.map((warning, idx) => (
                              <li key={idx}>{warning}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}

                    {bundleResult.bundles.map(renderBundleCard)}
                  </div>
                )}
              </div>
            </Card>
          </TabsContent>

          {/* ---------- SEARCH TAB ---------- */}
          <TabsContent value="search">
            <Card className="p-6">
              <div className="flex gap-2 mb-6">
                <Input
                  placeholder="e.g., birthday gift for mom"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !loading && searchGifts()}
                  disabled={loading}
                  className="flex-1"
                />
                <Button onClick={searchGifts} disabled={loading || !searchQuery.trim()}>
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <><Search className="h-5 w-5 mr-2" /> Search</>}
                </Button>
              </div>

              {searchResult?.success && searchResult.bundles.length > 0 && (
                <div className="space-y-8">
                  <Alert className="bg-blue-50 border-blue-200">
                    <Search className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-800">
                      Found {searchResult.count} result{searchResult.count !== 1 ? "s" : ""} for "{searchResult.query}"
                      {searchResult.metadata?.enrichment_stats && (
                        <span className="ml-2 text-sm">
                          ({searchResult.metadata.enrichment_stats.found_items}/{searchResult.metadata.enrichment_stats.total_items} items matched)
                        </span>
                      )}
                    </AlertDescription>
                  </Alert>

                  {/* Warnings if present */}
                  {searchResult.warnings && searchResult.warnings.length > 0 && (
                    <Alert className="bg-yellow-50 border-yellow-200">
                      <Info className="h-4 w-4 text-yellow-600" />
                      <AlertDescription className="text-yellow-800">
                        <p className="font-semibold mb-1">Search notes:</p>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {searchResult.warnings.map((warning, idx) => (
                            <li key={idx}>{warning}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Render bundles */}
                  {searchResult.bundles.map(renderBundleCard)}
                </div>
              )}

              {searchResult?.success && searchResult.bundles.length === 0 && (
                <div className="text-center py-12">
                  <Search className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                  <p className="text-gray-500">No results found for "{searchResult.query}"</p>
                  <p className="text-sm text-gray-400 mt-2">Try different keywords</p>
                </div>
              )}
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}