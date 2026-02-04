import { Popup } from "react-leaflet";
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "@/components/ui/card";

interface MapPopupCardProps {
    title: string;
    description?: string;
    children?: React.ReactNode;
}

export function MapPopupCard({ title, description, children }: MapPopupCardProps) {
    return (
        <Popup className="leaflet-popup-shadcn">
            <Card size="sm" className="border-none shadow-none ring-0 min-w-50">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm leading-tight">{title}</CardTitle>
                    {description && (
                        <CardDescription>{description}</CardDescription>
                    )}
                </CardHeader>
                {children && (
                    <CardContent className="pt-0">{children}</CardContent>
                )}
            </Card>
        </Popup>
    );
}
