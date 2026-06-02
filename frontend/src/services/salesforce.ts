import { get } from "../utils/requests";
import type { SalesforceNote } from "../types/salesforce";

/**
 * Fetch the Salesforce notes for an Account. Returns [] on error or no notes
 * (the popup treats empty as "no notes").
 */
export async function getAccountNotes(accountId: string): Promise<SalesforceNote[]> {
    const response = await get(`/salesforce/notes/?account_id=${encodeURIComponent(accountId)}`);
    return Array.isArray(response?.notes) ? response.notes : [];
}
