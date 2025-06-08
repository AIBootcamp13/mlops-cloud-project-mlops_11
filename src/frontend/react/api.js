import axios from 'axios';

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT;

export async function getRecommendContents(k) {
  try {
    console.log(API_ENDPOINT)
    const response = await axios.get(`${API_ENDPOINT}`, {
      params: {
        k: k,
      },
    });
    console.log(response)
    return response.data.recommended_content_id;
  } catch (error) {
    console.error('API Error:', error);
    return [];
  }
}
