export interface FeedbackRecord {
    id: string;
    intent: string;
    model: string;
    rating: number;
    feedbackText: string;
    createdAt: string;
}
export declare function logFeedback(intent: string, model: string, rating: number, feedbackText?: string): FeedbackRecord;
//# sourceMappingURL=rlhf.d.ts.map