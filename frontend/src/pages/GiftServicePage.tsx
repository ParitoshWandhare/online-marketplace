// src/pages/GiftServicePage.tsx
import { useState } from "react";
import {
  giftAiService,
  GiftBundle,
  BundleItem,
  GenerateBundleResponse,
  SearchResponse,
  VisionResponse,
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
  Brush,
  Star,
  IndianRupee,
  ShieldAlert,
  Calendar,
  AlertCircle,
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
  const [visionResult, setVisionResult] = useState<(VisionResponse & { type: string }) | null>(null);

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
      setError("Image size must be less than 5 MB");
      return;
    }

    setImageFile(file);
    setError("");
    console.log("Image uploaded (Vision tab):", file.name);
  };

  // -----------------------------------------------------------------------
  // BUNDLE GENERATION
  // -----------------------------------------------------------------------
  const generateBundle = async () => {
    if (!imageFile) return setError("Please upload an image first");

    setLoading(true);
    setError("");
    setBundleResult(null);

    try {
      console.log("Generating bundle from image…");
      const res = await giftAiService.generateGiftBundle(imageFile);
      console.log("Bundle result:", res);

      if (!res.success || !res.bundles?.length) {
        setError(res.message || "No bundles generated");
        return;
      }
      setBundleResult(res);
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
  // VISION ANALYSIS (with DEBUG LOGS)
  // -----------------------------------------------------------------------
  const runVisionAnalysis = async (type: string) => {
    if (!imageFile) return setError("Upload an image first");

    setLoading(true);
    setError("");
    setVisionResult(null);

    console.log(`[VISION] Starting ${type} analysis…`);
    console.log("[VISION] Image file:", imageFile.name, imageFile.size, "bytes");

    try {
      let result: VisionResponse;

      switch (type) {
        case "craft":
          result = await giftAiService.analyzeCraft(imageFile);
          break;
        case "quality":
          result = await giftAiService.analyzeQuality(imageFile);
          break;
        case "price":
          result = await giftAiService.estimatePrice(imageFile);
          break;
        case "fraud":
          result = await giftAiService.detectFraud(imageFile);
          break;
        case "occasion":
          result = await giftAiService.detectOccasion(imageFile);
          break;
        default:
          throw new Error("Invalid analysis type");
      }

      console.log(`[VISION] ${type} raw response:`, result);

      if (!result.success) {
        setError(result.message || `${type} analysis failed`);
        return;
      }

      setVisionResult({ type, ...result });
      console.log(`[VISION] ${type} analysis succeeded`);
    } catch (e: any) {
      console.error(`[VISION] ${type} error:`, e);
      setError(e.message || "Analysis failed");
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
          {bundle.bundle_name || `Bundle ${idx + 1}`}
        </h3>
        {bundle.description && <p className="text-sm text-gray-700">{bundle.description}</p>}
        {bundle.theme && <Badge variant="secondary" className="mt-2">{bundle.theme}</Badge>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {bundle.items?.map((item, i) => {
          const artwork = item.artwork;
          const id = item.mongo_id || artwork?._id || `b${idx}-i${i}`;
          const title = artwork?.title || item.title || "Untitled";
          const price = artwork?.price ?? item.price ?? 0;
          const img = artwork?.media?.[0]?.url;
          const reason = item.reason || "Perfect gift idea.";

          return (
            <div key={id} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow">
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
                  {id && !id.startsWith("b") && (
                    <Link to={`/artwork/${id}`} className="text-xs text-purple-600 hover:underline">
                      View Details
                    </Link>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {bundle.total_price ? (
        <div className="mt-6 pt-4 border-t border-purple-200 flex justify-between">
          <span className="text-lg font-semibold">Bundle Total:</span>
          <span className="text-2xl font-bold text-purple-600 flex items-center">
            <IndianRupee className="w-5 h-5 mr-1" />
            {bundle.total_price.toLocaleString("en-IN")}
          </span>
        </div>
      ) : null}
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
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="bundle">Generate Bundle</TabsTrigger>
            <TabsTrigger value="search">Text Search</TabsTrigger>
            <TabsTrigger value="vision">Vision AI</TabsTrigger>
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
                        <p className="text-sm text-gray-500">JPG, PNG up to 5 MB</p>
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

                {bundleResult?.success && bundleResult.bundles.length > 0 && (
                  <div className="space-y-8">
                    <Alert className="bg-green-50 border-green-200">
                      <Sparkles className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        Generated {bundleResult.bundles.length} bundle{bundleResult.bundles.length > 1 ? "s" : ""}!
                      </AlertDescription>
                    </Alert>
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
                    </AlertDescription>
                  </Alert>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {searchResult.bundles.flatMap((bundle, bIdx) =>
                      (bundle.items || []).map((item, iIdx) => {
                        const title = item.title || "Untitled Gift";
                        const reason = item.reason || "A thoughtful gift idea.";
                        const price = item.price ?? 0;
                        const similarity = item.similarity;
                        const mongoId = item.mongo_id;
                        const img = item.artwork?.media?.[0]?.url;

                        return (
                          <div
                            key={`${bIdx}-${iIdx}-${mongoId || title}`}
                            className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow"
                          >
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
                              {similarity !== undefined && (
                                <Badge variant="outline" className="text-xs">
                                  {(similarity * 100).toFixed(0)}% match
                                </Badge>
                              )}
                              <div className="flex justify-between items-center pt-2 border-t">
                                <p className="text-purple-600 font-bold text-sm flex items-center">
                                  <IndianRupee className="w-3 h-3 mr-1" />
                                  {typeof price === "number" ? price.toLocaleString("en-IN") : price}
                                </p>
                                {mongoId && (
                                  <Link to={`/artwork/${mongoId}`} className="text-xs text-purple-600 hover:underline">
                                    View Details
                                  </Link>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
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

         {/* ==================== VISION TAB ==================== */}
{/* ==================== VISION TAB ==================== */}
<TabsContent value="vision">
  <Card className="p-6">
    {/* Image Upload */}
    <div className="mb-8">
      <div className="border-2 border-dashed border-purple-300 rounded-xl p-10 text-center bg-gradient-to-br from-purple-50 to-pink-50 hover:border-purple-400 transition-colors">
        <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" id="vision-img" />
        <label htmlFor="vision-img" className="cursor-pointer block">
          {imageFile ? (
            <div className="space-y-4">
              <img
                src={URL.createObjectURL(imageFile)}
                alt="Uploaded"
                className="mx-auto max-h-64 rounded-lg shadow-md object-contain"
              />
              <p className="text-sm font-medium">{imageFile.name}</p>
              <p className="text-xs text-gray-500">Click to change</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="mx-auto w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center">
                <ImageIcon className="w-10 h-10 text-purple-600" />
              </div>
              <p className="text-lg font-semibold">Upload an image to analyze</p>
              <p className="text-sm text-gray-500">JPG, PNG up to 5MB</p>
            </div>
          )}
        </label>
      </div>
    </div>

    {/* Analysis Buttons */}
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
      {[
        { type: "craft", label: "Craft Type", icon: <Brush className="w-6 h-6" />, color: "text-blue-600", bg: "bg-blue-50" },
        { type: "quality", label: "Quality", icon: <Star className="w-6 h-6" />, color: "text-yellow-600", bg: "bg-yellow-50" },
        { type: "price", label: "Estimate Price", icon: <IndianRupee className="w-6 h-6" />, color: "text-green-600", bg: "bg-green-50" },
        { type: "fraud", label: "Fraud Check", icon: <ShieldAlert className="w-6 h-6" />, color: "text-red-600", bg: "bg-red-50" },
        { type: "occasion", label: "Occasion", icon: <Calendar className="w-6 h-6" />, color: "text-purple-600", bg: "bg-purple-50" },
      ].map((tool) => (
        <Button
          key={tool.type}
          variant="outline"
          onClick={() => runVisionAnalysis(tool.type)}
          disabled={!imageFile || loading}
          className={`h-24 flex flex-col items-center justify-center gap-2 hover:border-purple-400 hover:bg-purple-50 transition-all ${tool.bg} border-2`}
        >
          <div className={tool.color}>{tool.icon}</div>
          <span className="text-xs font-semibold">{tool.label}</span>
        </Button>
      ))}
    </div>

    {/* Loading State */}
    {loading && (
      <div className="flex flex-col items-center justify-center py-12 space-y-3">
        <Loader2 className="h-10 w-10 animate-spin text-purple-600" />
        <p className="text-lg font-medium text-purple-700">Analyzing image with AI...</p>
        <p className="text-sm text-gray-500">This may take a few seconds</p>
      </div>
    )}

    {/* Result Display */}
    {visionResult?.success && !loading && (
      <div className="space-y-6 animate-fade-in">

        {/* === QUALITY ANALYSIS === */}
        {visionResult.type === "quality" && visionResult.data && (
          <Card className="p-6 bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200 shadow-lg">
            <h3 className="text-2xl font-bold text-amber-800 mb-5 flex items-center gap-2">
              <Star className="w-7 h-7 text-amber-600 fill-amber-600" />
              Quality Assessment
            </h3>

            {/* Star Rating */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => {
                  const rating = visionResult.data.quality_rating || 
                                 (visionResult.data.craftsmanship_score ? Math.round(visionResult.data.craftsmanship_score * 5) : 0);
                  return (
                    <Star
                      key={star}
                      className={`w-8 h-8 transition-all ${
                        star <= rating
                          ? "text-amber-500 fill-amber-500"
                          : "text-gray-300"
                      }`}
                    />
                  );
                })}
              </div>
              <span className="text-lg font-semibold text-amber-900">
                {(() => {
                  const score = visionResult.data.craftsmanship_score;
                  const rating = visionResult.data.quality_rating || (score ? Math.round(score * 5) : 0);
                  return `${rating}/5`;
                })()}
              </span>
            </div>

            {/* Craftsmanship Score Progress */}
            {visionResult.data.craftsmanship_score !== undefined && (
              <div className="mb-5">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-amber-800">Craftsmanship</span>
                  <span className="font-semibold text-amber-900">
                    {(visionResult.data.craftsmanship_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-amber-500 to-yellow-500 h-3 rounded-full transition-all duration-700"
                    style={{ width: `${(visionResult.data.craftsmanship_score * 100).toFixed(0)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Quality Label */}
            <div className="mb-4">
              <Badge
                className={`text-lg px-4 py-1 ${
                  visionResult.data.quality === "high"
                    ? "bg-green-100 text-green-800"
                    : visionResult.data.quality === "medium"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {visionResult.data.quality?.toUpperCase() || "UNKNOWN"} QUALITY
              </Badge>
            </div>

            {/* Detailed Description */}
            {visionResult.data.details && (
              <div className="bg-white/70 p-4 rounded-lg border border-amber-200">
                <p className="text-sm text-amber-800 leading-relaxed italic">
                  {visionResult.data.details}
                </p>
              </div>
            )}
          </Card>
        )}

        {/* === CRAFT TYPE === */}
        {visionResult.type === "craft" && visionResult.data && (
          <Card className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
              <Brush className="w-5 h-5" /> Detected Craft Style
            </h4>
            <p className="text-lg font-medium text-blue-900">
              {visionResult.data.craft_type || "Unknown Craft"}
            </p>
            {visionResult.data.confidence && (
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${(visionResult.data.confidence * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-blue-700">
                  {(visionResult.data.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {visionResult.data.description && (
              <p className="text-sm text-blue-700 mt-2 italic">{visionResult.data.description}</p>
            )}
          </Card>
        )}

        {/* === PRICE === */}
        {visionResult.type === "price" && visionResult.data && (
          <Card className="p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
            <h4 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
              <IndianRupee className="w-5 h-5" /> Estimated Market Price
            </h4>
            <p className="text-3xl font-bold text-green-700 text-center">
              ₹{(visionResult.data.estimated_price || 0).toLocaleString("en-IN")}
            </p>
            {visionResult.data.price_range && (
              <p className="text-sm text-green-600 text-center mt-1">
                Range: ₹{visionResult.data.price_range.min} – ₹{visionResult.data.price_range.max}
              </p>
            )}
          </Card>
        )}

        {/* === FRAUD === */}
        {visionResult.type === "fraud" && visionResult.data && (
          <Card className={`p-5 border-2 ${visionResult.data.is_fraudulent ? "bg-red-50 border-red-300" : "bg-green-50 border-green-300"}`}>
            <h4 className={`font-semibold mb-3 flex items-center gap-2 ${visionResult.data.is_fraudulent ? "text-red-800" : "text-green-800"}`}>
              <ShieldAlert className="w-5 h-5" /> Fraud Risk
            </h4>
            <p className={`text-2xl font-bold text-center ${visionResult.data.is_fraudulent ? "text-red-700" : "text-green-700"}`}>
              {visionResult.data.is_fraudulent ? "High Risk" : "Low Risk"}
            </p>
            {visionResult.data.red_flags?.length > 0 && (
              <div className="mt-3 space-y-1">
                {visionResult.data.red_flags.map((flag: string, i: number) => (
                  <p key={i} className="text-xs text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {flag}
                  </p>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* === OCCASION === */}
        {visionResult.type === "occasion" && visionResult.data && (
          <Card className="p-5 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
            <h4 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
              <Calendar className="w-5 h-5" /> Best For Occasion
            </h4>
            <p className="text-xl font-semibold text-purple-900">
              {visionResult.data.occasion || "General Gifting"}
            </p>
            {visionResult.data.suggested_events?.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {visionResult.data.suggested_events.map((event: string, i: number) => (
                  <Badge key={i} variant="secondary" className="bg-purple-100 text-purple-700">
                    {event}
                  </Badge>
                ))}
              </div>
            )}
          </Card>
        )}

      </div>
    )}

    {/* Empty State */}
    {!loading && !visionResult && (
      <div className="text-center py-16 text-gray-500">
        <div className="mx-auto w-24 h-24 bg-purple-100 rounded-full flex items-center justify-center mb-4">
          <Sparkles className="w-12 h-12 text-purple-400" />
        </div>
        <p className="text-lg font-medium">Upload an image and select an analysis</p>
        <p className="text-sm mt-1">Get instant AI insights in seconds</p>
      </div>
    )}
  </Card>
</TabsContent>
        </Tabs>
      </div>
    </div>
  );
}